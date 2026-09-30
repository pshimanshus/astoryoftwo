"""Optional DeepEval shadow metrics behind deterministic carousel gates.

The adapter uses standalone ``metric.measure`` calls. It never logs in to
Confident AI, never reads dotenv files, and never becomes a release gate.
Provider calls require a repo-specific opt-in plus a process credential.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Mapping


# Set these before importing deepeval. Current releases otherwise search local
# dotenv files and emit anonymous product telemetry.
os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "1"

SHADOW_METRICS = (
    "prompt_adherence",
    "task_completion",
    "tool_trajectory_correctness",
    "image_coherence",
    "prompt_image_alignment",
    "reference_aware_visual_comparison",
    "creator_recognition",
    "relationship_proof",
)
DEEPEVAL_TESTED_VERSION = "4.2.1"
MIN_CALIBRATION_OUTPUTS = 20
MIN_CALIBRATION_PACKAGES = 5
MAX_HARD_FAIL_DISAGREEMENT = 0.10
_SHA256_RE = re.compile(r"(?:sha256:)?[0-9a-f]{64}")
_PACKAGE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,299}")
_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:pk|sk)-lf-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(?:api[_ -]?key|secret|token|password)\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{8,}\d)(?!\w)"),
)


def _normalize_sha256(value: object) -> str | None:
    candidate = str(value or "").strip().lower()
    if not _SHA256_RE.fullmatch(candidate):
        return None
    return candidate.removeprefix("sha256:")


def _sdk_installed(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return module in __import__("sys").modules


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def calibration_status(root: Path) -> dict[str, Any]:
    """Validate, but never create or repair, human calibration evidence."""

    workspace = root.resolve()
    valid: dict[str, dict[str, Any]] = {}
    invalid: list[dict[str, Any]] = []
    duplicate_hashes: set[str] = set()
    for path in sorted((workspace / "evals" / "calibration").glob("*.json")):
        reasons: list[str] = []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            payload = None
            reasons.append("invalid_json")
        if not isinstance(payload, dict):
            if not reasons:
                reasons.append("record_must_be_object")
        else:
            output_sha256 = _normalize_sha256(payload.get("output_sha256"))
            package_id = str(payload.get("package_id") or "").strip()
            output_path = str(payload.get("output_path") or "").strip()
            if output_sha256 is None:
                reasons.append("invalid_output_sha256")
            if not _PACKAGE_ID_RE.fullmatch(package_id) or ".." in Path(package_id).parts:
                reasons.append("invalid_package_id")
            package = Path(package_id)
            if package.is_absolute():
                reasons.append("invalid_package_id")
            output = Path(output_path)
            if not output_path or output.is_absolute() or ".." in output.parts:
                reasons.append("invalid_output_path")
            if payload.get("creator_reviewed") is not True:
                reasons.append("not_creator_reviewed")
            if not isinstance(payload.get("creator_hard_fail"), bool):
                reasons.append("creator_hard_fail_must_be_boolean")
            if not isinstance(payload.get("judge_hard_fail"), bool):
                reasons.append("judge_hard_fail_must_be_boolean")
            if not reasons:
                try:
                    package_resolved = (workspace / package).resolve(strict=True)
                    output_resolved = (workspace / output).resolve(strict=True)
                    package_resolved.relative_to(workspace)
                    output_resolved.relative_to(package_resolved)
                    if not package_resolved.is_dir() or not output_resolved.is_file():
                        raise ValueError
                    actual_sha256 = _file_sha256(output_resolved)
                    if actual_sha256 != output_sha256:
                        reasons.append("output_sha256_mismatch")
                except (OSError, ValueError):
                    reasons.append("output_artifact_unavailable")
            if not reasons and output_sha256 is not None:
                comparable = {
                    "output_sha256": output_sha256,
                    "package_id": package_id,
                    "output_path": output_path,
                    "creator_hard_fail": payload["creator_hard_fail"],
                    "judge_hard_fail": payload["judge_hard_fail"],
                }
                existing = valid.get(output_sha256)
                if existing is None:
                    valid[output_sha256] = comparable
                elif existing != comparable:
                    duplicate_hashes.add(output_sha256)
        if reasons:
            invalid.append(
                {
                    "path": path.relative_to(workspace).as_posix(),
                    "reasons": sorted(set(reasons)),
                }
            )

    # Conflicting reviews for one output cannot be resolved by file order.
    for output_sha256 in duplicate_hashes:
        valid.pop(output_sha256, None)
    comparable = list(valid.values())
    packages = {item["package_id"] for item in comparable}
    disagreements = sum(
        item["creator_hard_fail"] != item["judge_hard_fail"]
        for item in comparable
    )
    rate = disagreements / len(comparable) if comparable else None
    calibrated = bool(
        len(comparable) >= MIN_CALIBRATION_OUTPUTS
        and len(packages) >= MIN_CALIBRATION_PACKAGES
        and rate is not None
        and rate < MAX_HARD_FAIL_DISAGREEMENT
    )
    return {
        "calibrated": calibrated,
        "reviewed_outputs": len(comparable),
        "package_count": len(packages),
        "hard_fail_disagreements": disagreements,
        "hard_fail_disagreement_rate": rate,
        "required_outputs": MIN_CALIBRATION_OUTPUTS,
        "required_packages": MIN_CALIBRATION_PACKAGES,
        "maximum_disagreement_rate_exclusive": MAX_HARD_FAIL_DISAGREEMENT,
        "invalid_record_count": len(invalid),
        "invalid_records": invalid,
        "conflicting_output_count": len(duplicate_hashes),
        "evidence_policy": "read_only_human_reviews_only",
        "artifact_policy": "existing_workspace_output_bound_by_sha256",
    }


def deepeval_environment_status() -> dict[str, Any]:
    """Report readiness without importing the SDK or exposing credentials."""

    try:
        installed_version = importlib.metadata.version("deepeval")
    except importlib.metadata.PackageNotFoundError:
        installed_version = None
    return {
        "enabled": os.environ.get("ASOT_DEEPEVAL_ENABLED") == "1",
        "sdk_installed": _sdk_installed("deepeval"),
        "sdk_version": installed_version,
        "tested_sdk_version": DEEPEVAL_TESTED_VERSION,
        "evaluator_credentials_present": bool(os.environ.get("OPENAI_API_KEY")),
        "external_media_enabled": os.environ.get("ASOT_DEEPEVAL_ALLOW_MEDIA") == "1",
        "dotenv_disabled": os.environ.get("DEEPEVAL_DISABLE_DOTENV") == "1",
        "telemetry_disabled": os.environ.get("DEEPEVAL_TELEMETRY_OPT_OUT") == "1",
        "install_command": f"python -m pip install 'deepeval=={DEEPEVAL_TESTED_VERSION}'",
        "isolated_setup_command": "make feedback-integrations-setup",
    }


def run_deepeval_sdk_smoke() -> dict[str, Any]:
    """Construct the real adapter metrics with an offline local model."""

    environment = deepeval_environment_status()
    if not environment["sdk_installed"]:
        return {
            "status": "not_run",
            "reason": "deepeval is not installed",
            "coverage": "none",
            "external_calls": "none",
        }
    try:
        from deepeval.metrics import GEval, ImageCoherenceMetric, TextToImageMetric  # type: ignore
        from deepeval.models import DeepEvalBaseLLM  # type: ignore
        from deepeval.test_case import LLMTestCase, MLLMImage  # type: ignore
        from deepeval.utils import convert_to_multi_modal_array  # type: ignore
        try:
            from deepeval.test_case import SingleTurnParams as EvalParams  # type: ignore
        except ImportError:
            from deepeval.test_case import LLMTestCaseParams as EvalParams  # type: ignore

        class OfflineContractModel(DeepEvalBaseLLM):
            def load_model(self, *args: Any, **kwargs: Any) -> Any:
                return self

            def get_model_name(self, *args: Any, **kwargs: Any) -> str:
                return "asot-offline-contract"

            def generate(self, *args: Any, **kwargs: Any) -> str:
                raise RuntimeError("offline contract smoke never generates")

            async def a_generate(self, *args: Any, **kwargs: Any) -> str:
                raise RuntimeError("offline contract smoke never generates")

        model = OfflineContractModel()
        metrics = [
            GEval(
                name="adapter_contract_smoke",
                criteria="Validate constructor compatibility only.",
                evaluation_params=[EvalParams.INPUT, EvalParams.ACTUAL_OUTPUT],
                model=model,
                threshold=None,
                async_mode=False,
            ),
            ImageCoherenceMetric(model=model, threshold=None, async_mode=False),
            TextToImageMetric(model=model, threshold=None, async_mode=False),
        ]
        image = MLLMImage(
            dataBase64=(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
                "+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
            mimeType="image/png",
        )
        case = LLMTestCase(input="sdk-smoke", actual_output=f"{image}")
        multimodal_parts = convert_to_multi_modal_array(case.actual_output)
        if (
            [type(metric).__name__ for metric in metrics]
            != ["GEval", "ImageCoherenceMetric", "TextToImageMetric"]
            or case.multimodal is not True
            or not any(isinstance(part, MLLMImage) for part in multimodal_parts)
            or model.get_model_name() != "asot-offline-contract"
        ):
            raise ValueError("unexpected installed SDK contract")
    except Exception as exc:
        return {
            "status": "failed",
            "reason": type(exc).__name__,
            "coverage": "real_metric_construction_offline_model_and_multimodal_token",
            "external_calls": "none",
            "sdk_version": environment["sdk_version"],
        }
    return {
        "status": "passed",
        "coverage": "real_metric_construction_offline_model_and_multimodal_token",
        "external_calls": "none",
        "sdk_version": environment["sdk_version"],
    }


def _not_run(reason: str, *, root: Path) -> dict[str, Any]:
    return {
        "mode": "shadow",
        "status": "not_run",
        "reason": reason,
        "metrics": [{"name": name, "status": "not_run"} for name in SHADOW_METRICS],
        "calibration": calibration_status(root),
        "environment": deepeval_environment_status(),
        "can_gate": False,
    }


def _redact_external_text(value: object, *, limit: int = 20_000) -> str:
    text = str(value or "")[:limit]
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    text = re.sub(r"(?<!\w)/(?:[^\s/]+/)+[^\s]+", "[LOCAL_PATH]", text)
    return text


def _safe_local_images(root: Path, paths: list[str] | None) -> list[str]:
    workspace = root.resolve(strict=True)
    resolved: list[str] = []
    for value in paths or []:
        supplied = Path(str(value)).expanduser()
        candidate = supplied if supplied.is_absolute() else workspace / supplied
        if candidate.is_symlink():
            raise ValueError("image inputs cannot be symlinks")
        candidate = candidate.resolve(strict=True)
        try:
            candidate.relative_to(workspace)
        except ValueError as exc:
            raise ValueError("image inputs must stay inside the workspace") from exc
        if not candidate.is_file() or candidate.suffix.casefold() not in _IMAGE_SUFFIXES:
            raise ValueError("image inputs must be supported regular image files")
        resolved.append(str(candidate))
    return resolved


def run_deepeval_shadow(
    root: Path,
    *,
    prompt: str,
    actual_output: str,
    expected_output: str = "",
    context: list[str] | None = None,
    image_paths: list[str] | None = None,
    reference_paths: list[str] | None = None,
    trajectory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run advisory metrics only after explicit enablement and credential checks."""

    os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "1"
    root = root.resolve()
    if os.environ.get("ASOT_DEEPEVAL_ENABLED") != "1":
        return _not_run("DeepEval shadow evaluation is disabled", root=root)
    if not os.environ.get("OPENAI_API_KEY"):
        return _not_run("missing evaluator credentials", root=root)
    try:
        images = _safe_local_images(root, image_paths)
        references = _safe_local_images(root, reference_paths)
    except (OSError, ValueError):
        return _not_run("image or reference input unavailable", root=root)
    try:
        from deepeval.metrics import GEval, ImageCoherenceMetric, TextToImageMetric  # type: ignore
        from deepeval.test_case import LLMTestCase, MLLMImage  # type: ignore
        try:
            from deepeval.test_case import SingleTurnParams as EvalParams  # type: ignore
        except ImportError:  # DeepEval < 4 compatibility
            from deepeval.test_case import LLMTestCaseParams as EvalParams  # type: ignore
    except Exception as exc:
        reason = "deepeval is not installed" if isinstance(exc, ImportError) else (
            f"deepeval SDK unavailable: {type(exc).__name__}"
        )
        return _not_run(reason, root=root)
    media_enabled = os.environ.get("ASOT_DEEPEVAL_ALLOW_MEDIA") == "1"
    if not media_enabled:
        images = []
        references = []

    prompt_text = _redact_external_text(prompt)
    output_text = _redact_external_text(actual_output)
    expected_text = _redact_external_text(expected_output)
    context_text = [_redact_external_text(item, limit=4_000) for item in context or []]
    trajectory_text = _redact_external_text(
        json.dumps(trajectory, ensure_ascii=False, sort_keys=True) if trajectory else "",
        limit=12_000,
    )
    image_tokens = [str(MLLMImage(url=path, local=True)) for path in images]
    reference_tokens = [str(MLLMImage(url=path, local=True)) for path in references]
    visual_output = output_text + ("\n" + "\n".join(image_tokens) if image_tokens else "")
    visual_input = prompt_text + ("\n" + "\n".join(reference_tokens) if reference_tokens else "")
    case = LLMTestCase(
        input=visual_input,
        actual_output=visual_output
        + ("\nOrdered tool trajectory:\n" + trajectory_text if trajectory_text else ""),
        expected_output=expected_text or None,
        context=context_text or None,
    )
    results: list[dict[str, Any]] = []
    metric_prompts = {
        "prompt_adherence": "Does the output satisfy every explicit prompt constraint?",
        "task_completion": "Does the output complete the requested carousel-generation task?",
        "tool_trajectory_correctness": "Does the described trajectory generate, ingest, inspect, and review pixels in order?",
        "creator_recognition": "Would the intended creator audience recognize the specified private couple moment?",
        "relationship_proof": "Does the output visibly prove the relationship beat through observable action?",
        "reference_aware_visual_comparison": "Compare the generated image with the supplied references. Assess whole-person identity, style, proportions, and required preserved attributes without rewarding unrelated visual similarity.",
    }
    for name in SHADOW_METRICS:
        visual_metric = name in {
            "image_coherence",
            "prompt_image_alignment",
            "reference_aware_visual_comparison",
            "creator_recognition",
            "relationship_proof",
        }
        if visual_metric and not images:
            reason = (
                "external media is not enabled"
                if (image_paths or reference_paths) and not media_enabled
                else "missing actual image input"
            )
            results.append({"name": name, "status": "not_run", "reason": reason})
            continue
        if name == "reference_aware_visual_comparison" and not references:
            results.append({"name": name, "status": "not_run", "reason": "missing reference image input"})
            continue
        if name == "tool_trajectory_correctness" and not trajectory:
            results.append({"name": name, "status": "not_run", "reason": "missing ordered tool trajectory"})
            continue
        try:
            if name == "image_coherence":
                metric = ImageCoherenceMetric(threshold=None, async_mode=False)
                metric_case = LLMTestCase(input=prompt_text, actual_output=visual_output)
            elif name == "prompt_image_alignment":
                if len(images) != 1:
                    results.append({"name": name, "status": "not_run", "reason": "TextToImageMetric requires exactly one generated image"})
                    continue
                metric = TextToImageMetric(threshold=None, async_mode=False)
                metric_case = LLMTestCase(input=prompt_text, actual_output=image_tokens[0])
            else:
                metric = GEval(
                    name=name,
                    criteria=metric_prompts[name],
                    evaluation_params=[EvalParams.INPUT, EvalParams.ACTUAL_OUTPUT],
                    threshold=None,
                    async_mode=False,
                )
                metric_case = case
            metric.measure(metric_case)
            score = float(metric.score)
            if not math.isfinite(score):
                raise ValueError("metric returned a non-finite score")
            results.append(
                {
                    "name": name,
                    "status": "scored",
                    "score": score,
                    "reason": _redact_external_text(getattr(metric, "reason", ""), limit=4_000),
                }
            )
        except Exception as exc:  # provider/library failure is advisory by contract
            results.append({"name": name, "status": "not_run", "reason": type(exc).__name__})
    calibration = calibration_status(root)
    return {
        "mode": "shadow",
        "status": "scored" if any(item["status"] == "scored" for item in results) else "not_run",
        "metrics": results,
        "calibration": calibration,
        "environment": deepeval_environment_status(),
        "external_payload_policy": "redacted_text; workspace media requires separate explicit opt-in",
        "can_gate": False,
    }


def run_feedback_case_shadow(root: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    return run_deepeval_shadow(
        root,
        prompt="\n".join(str(item) for item in case.get("must_change") or []),
        actual_output=json.dumps(case.get("checks") or [], ensure_ascii=False),
        expected_output="\n".join(str(item) for item in case.get("must_preserve") or []),
        context=[str(case.get("diagnosis") or "")],
    )


__all__ = [
    "DEEPEVAL_TESTED_VERSION",
    "MAX_HARD_FAIL_DISAGREEMENT",
    "MIN_CALIBRATION_OUTPUTS",
    "MIN_CALIBRATION_PACKAGES",
    "SHADOW_METRICS",
    "calibration_status",
    "deepeval_environment_status",
    "run_deepeval_sdk_smoke",
    "run_deepeval_shadow",
    "run_feedback_case_shadow",
]
