"""Bounded maker/checker loop for one evidence-backed Instagram idea.

The module owns deterministic loop state, evidence fingerprints, completion
validation, and the Codex CLI boundary. Creative invention and editorial
judgment remain with distinct read-only subagents. The successful terminal
state is ``READY_FOR_CONCEPT_LOCK``; publishing is deliberately out of scope.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


SCHEMA_VERSION = "1.0"
SUCCESS_STATUS = "READY_FOR_CONCEPT_LOCK"
HONEST_STOP_STATUSES = {
    "NO_GO",
    "STAGNATED",
    "BUDGET_EXHAUSTED",
    "STALE_EVIDENCE",
    "HUMAN_REQUIRED",
}

CORE_EVIDENCE_PATHS = (
    "config/skills/creator-skill-stack.md",
    "config/skills/carousel-jam-runtime-context.md",
    "memory/semantic/carousel-idea-preferences.md",
    "wiki/insights/successful-carousel-standard.md",
)

DYNAMIC_EVIDENCE_GLOBS = (
    "corpus/forensic-instagram/**/*",
    "corpus/competitors/**/*",
    "output/concepts/**/concept-selection.json",
    "output/carousels/**/concept-selection.json",
    "output/reports/*.md",
)

REQUIRED_SUCCESS_ARTIFACTS = (
    "source-memory-brief.json",
    "concept-routes.json",
    "concept-debate.json",
    "concept-repairs.json",
    "taste-gate.json",
    "verification.json",
    "concept-selection.json",
    "creator-brief.md",
)

REQUIRED_STOP_ARTIFACTS = (
    "source-memory-brief.json",
    "concept-routes.json",
    "verification.json",
    "creator-brief.md",
)

EVIDENCE_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".tsv", ".txt"}
MAX_EVIDENCE_FILE_BYTES = 5 * 1024 * 1024


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def candidate_fingerprint(candidate: dict[str, Any]) -> str:
    """Return a stable fingerprint for the exact candidate card under review."""

    payload = json.dumps(
        candidate,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def blind_candidate_card(candidate: dict[str, Any]) -> dict[str, Any]:
    """Remove author identity and persuasive metadata from a critic input."""

    hidden = {
        "maker_task_id",
        "maker_agent",
        "self_score",
        "self_scores",
        "maker_commentary",
    }
    return {key: value for key, value in candidate.items() if key not in hidden}


def blind_candidate_fingerprint(candidate: dict[str, Any]) -> str:
    return candidate_fingerprint(blind_candidate_card(candidate))


def _evidence_record(repo_root: Path, path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": _relative(repo_root, path),
        "exists": path.is_file(),
    }
    if not path.is_file():
        return record
    stat = path.stat()
    record.update(
        {
            "sha256": _sha256_file(path),
            "bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ).replace(microsecond=0).isoformat(),
        }
    )
    return record


def build_evidence_manifest(
    repo_root: Path,
    *,
    dynamic_limit: int = 40,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Snapshot the files agents may inspect without embedding their contents."""

    repo_root = repo_root.resolve()
    now = now or datetime.now(timezone.utc)
    core = [_evidence_record(repo_root, repo_root / relative) for relative in CORE_EVIDENCE_PATHS]

    dynamic_paths: dict[str, Path] = {}
    for pattern in DYNAMIC_EVIDENCE_GLOBS:
        for path in repo_root.glob(pattern):
            if (
                path.is_file()
                and path.suffix.lower() in EVIDENCE_SUFFIXES
                and path.stat().st_size <= MAX_EVIDENCE_FILE_BYTES
            ):
                dynamic_paths[_relative(repo_root, path)] = path
    newest_dynamic = sorted(
        dynamic_paths.values(),
        key=lambda path: (path.stat().st_mtime, str(path)),
        reverse=True,
    )[:dynamic_limit]
    dynamic = [_evidence_record(repo_root, path) for path in newest_dynamic]

    external_records = [
        record
        for record in dynamic
        if str(record["path"]).startswith(("corpus/forensic-instagram/", "corpus/competitors/"))
    ]
    newest_external_at: datetime | None = None
    for record in external_records:
        modified_at = record.get("modified_at")
        if not modified_at:
            continue
        parsed = datetime.fromisoformat(str(modified_at))
        newest_external_at = max(newest_external_at, parsed) if newest_external_at else parsed

    if newest_external_at is None:
        external_status = "MISSING"
        external_age_days = None
    else:
        external_age_days = max(0, (now - newest_external_at).days)
        external_status = "CURRENT" if external_age_days <= 30 else "STALE"

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": now.replace(microsecond=0).isoformat(),
        "repo_root": str(repo_root),
        "core": core,
        "dynamic": dynamic,
        "freshness": {
            "external_snapshot_status": external_status,
            "newest_external_snapshot_age_days": external_age_days,
            "stale_after_days": 30,
            "note": "Freshness is evidence context, not permission to invent missing signals.",
        },
    }


class LoopState(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    iteration: int = Field(ge=0)
    max_iterations: int = Field(ge=1, le=6)
    candidate_budget: int = Field(ge=4, le=12)
    seed: str | None = None
    final_candidate_id: str | None = None
    stop_reason: str = ""
    creator_approval: Literal["PENDING"] = "PENDING"
    history: list[dict[str, Any]] = Field(default_factory=list)


class IdeaCandidate(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: str = Field(min_length=1)
    iteration: int = Field(ge=1)
    maker_agent: Literal["asot_idea_maker"]
    maker_task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    concrete_moment: str = Field(min_length=1)
    universal_truth: str = Field(min_length=1)
    audience_mirror: str = Field(min_length=1)
    scroll_stop: str = Field(min_length=1)
    emotional_contradiction: str = Field(min_length=1)
    scene_proof: list[str] = Field(min_length=2)
    relationship_motion: str = Field(min_length=1)
    retention_ladder: list[str] = Field(min_length=2)
    payoff: str = Field(min_length=1)
    dm_send_reason: str = Field(min_length=1)
    format_recommendation: str = Field(min_length=1)
    asot_turn: str = Field(min_length=1)
    evidence_paths: list[str] = Field(min_length=1)
    novelty_fingerprint: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)


class CandidatePool(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    candidates: list[IdeaCandidate] = Field(min_length=1)


class StoryDirectorScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: int = Field(ge=0, le=10)
    story: int = Field(ge=0, le=10)
    bridge: int = Field(ge=0, le=10)
    relationship_motion: int = Field(ge=0, le=10)
    ending: int = Field(ge=0, le=10)
    dm_send: int = Field(ge=0, le=10)

    @property
    def passes(self) -> bool:
        return all(score >= 8 for score in self.model_dump().values())


class VerificationScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_selling: int = Field(ge=0, le=30)
    golden_theme: int = Field(ge=0, le=30)
    distribution: int = Field(ge=0, le=30)
    visual_generativity: int = Field(ge=0, le=30)
    story_director: StoryDirectorScores

    @property
    def passes(self) -> bool:
        return (
            self.story_selling >= 28
            and self.golden_theme >= 28
            and self.distribution >= 26
            and self.visual_generativity >= 27
            and self.story_director.passes
        )


class VerificationRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: str = Field(min_length=1)
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    blind_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    maker_task_id: str = Field(min_length=1)
    verifier_agent: Literal["asot_idea_verifier"]
    verifier_task_id: str = Field(min_length=1)
    scores: VerificationScores
    stage_scene_gate: Literal["PASS", "REPAIR", "STOP"]
    taste_gate: Literal["PASS_NO_CAP", "REPAIR", "STOP"]
    safety_gate: Literal["PASS", "REPAIR", "STOP"]
    exclusion_hits: list[str] = Field(default_factory=list)
    hard_failures: list[str] = Field(default_factory=list)
    verdict: Literal["PASS", "REPAIR", "STOP"]
    reasons: list[str] = Field(min_length=1)
    repair_instructions: list[str] = Field(default_factory=list)

    @property
    def satisfies_completion(self) -> bool:
        return (
            self.scores.passes
            and self.stage_scene_gate == "PASS"
            and self.taste_gate == "PASS_NO_CAP"
            and self.safety_gate == "PASS"
            and not self.exclusion_hits
            and not self.hard_failures
        )

    @model_validator(mode="after")
    def pass_must_be_earned(self) -> "VerificationRecord":
        if self.verdict == "PASS" and not self.satisfies_completion:
            raise ValueError("PASS cannot bypass thresholds, caps, exclusions, or hard failures")
        if self.maker_task_id == self.verifier_task_id:
            raise ValueError("maker and verifier task IDs must be distinct")
        return self


class SelectorRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    selector_agent: Literal["asot_idea_verifier"]
    selector_task_id: str = Field(min_length=1)
    candidate_id: str | None = None
    candidate_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    critic_task_ids: list[str] = Field(min_length=2)
    verdict: Literal["PASS", "NO_GO"]
    reasons: list[str] = Field(min_length=1)


class VerificationBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    reviews: list[VerificationRecord] = Field(min_length=1)
    selector: SelectorRecord


class ConceptSelection(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    selected_candidate_id: str | None = None
    selector_task_id: str = Field(min_length=1)
    creator_approval: Literal["PENDING"] = "PENDING"
    reason: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)


def artifact_schema() -> dict[str, Any]:
    """Expose the exact agent-written JSON contract without duplicating it in prompts."""

    return {
        "schema_version": SCHEMA_VERSION,
        "loop_state": LoopState.model_json_schema(),
        "concept_routes": CandidatePool.model_json_schema(),
        "verification": VerificationBundle.model_json_schema(),
        "concept_selection": ConceptSelection.model_json_schema(),
    }


@dataclass(frozen=True)
class IdeaLoopConfig:
    max_iterations: int = 3
    candidate_budget: int = 6
    command_timeout_seconds: int = 1800
    live_search: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.max_iterations <= 6:
            raise ValueError("max_iterations must be between 1 and 6")
        if not 4 <= self.candidate_budget <= 12:
            raise ValueError("candidate_budget must be between 4 and 12")
        if self.command_timeout_seconds < 1:
            raise ValueError("command_timeout_seconds must be positive")


@dataclass(frozen=True)
class ValidationReport:
    run_dir: str
    status: str
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_dir": self.run_dir,
            "status": self.status,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def allocate_run_dir(
    repo_root: Path,
    *,
    requested: Path | None = None,
    now: datetime | None = None,
) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    now = now or datetime.now().astimezone()
    base = repo_root / "output" / "idea-loops" / now.strftime("%Y-%m-%d")
    stem = now.strftime("run-%H%M%S")
    candidate = base / stem
    suffix = 2
    while candidate.exists():
        candidate = base / f"{stem}-{suffix}"
        suffix += 1
    return candidate.resolve()


def build_orchestration_prompt(
    *,
    run_dir: Path,
    config: IdeaLoopConfig,
    seed: str | None,
) -> str:
    seed_line = seed if seed else "No seed supplied. Discover a fresh opportunity from repo evidence."
    return f"""Use $a-story-instagram-idea-loop to run one bounded Instagram idea loop.

Exact run directory (the only path you may write):
{run_dir}

Seed:
{seed_line}

Budgets:
- maximum iterations: {config.max_iterations}
- maximum candidates per iteration: {config.candidate_budget}

Read `.internal/loop-state.json` and `.internal/evidence-manifest.json` inside
the run directory first. Load the exact artifact field contract with:
venv/bin/python scripts/instagram_idea_loop.py schema

Follow the skill exactly. Use project custom agents
`asot_idea_scout`, `asot_idea_maker`, and `asot_idea_verifier`; the controller
must not impersonate their independent outputs. Spawn two maker tasks with
different creative lanes, two blind verifier tasks with different lenses, and
a fresh selector task. Give critics only the author-hidden card produced by the
schema contract and bind their reviews to both the exact candidate and blind
input fingerprints. The controller alone writes artifacts.

Iterate generate -> blind verify -> scoped repair -> fresh verify until one
route satisfies every stop condition or an honest terminal state is reached.
Never lower thresholds, expose below-threshold routes in `creator-brief.md`,
invent creator approval, package a carousel, generate images, publish, edit
durable memory, or claim guaranteed virality. On success stop at
READY_FOR_CONCEPT_LOCK with creator approval PENDING.

Before finishing, run:
venv/bin/python scripts/instagram_idea_loop.py validate {run_dir}
Repair contract errors within the remaining budget. If they cannot be repaired,
write an honest stop reason rather than fabricating a pass.
"""


def prepare_run(
    repo_root: Path,
    *,
    config: IdeaLoopConfig,
    seed: str | None = None,
    run_dir: Path | None = None,
    now: datetime | None = None,
) -> Path:
    repo_root = repo_root.resolve()
    destination = allocate_run_dir(repo_root, requested=run_dir, now=now)
    internal = destination / ".internal"
    internal.mkdir(parents=True, exist_ok=False)
    run_id = destination.name
    evidence = build_evidence_manifest(repo_root, now=now)
    state = LoopState(
        run_id=run_id,
        status="RUNNING",
        stage="DISCOVER",
        iteration=0,
        max_iterations=config.max_iterations,
        candidate_budget=config.candidate_budget,
        seed=seed,
        history=[
            {
                "at": _now_iso(),
                "stage": "DISCOVER",
                "event": "run_prepared",
            }
        ],
    )
    _write_json(internal / "evidence-manifest.json", evidence)
    _write_json(internal / "loop-state.json", state.model_dump(mode="json"))
    (internal / "orchestration-prompt.md").write_text(
        build_orchestration_prompt(
            run_dir=destination,
            config=config,
            seed=seed,
        ),
        encoding="utf-8",
    )
    return destination


def update_loop_state(
    run_dir: Path,
    *,
    status: str,
    stage: str,
    stop_reason: str | None = None,
    event: str,
) -> LoopState:
    state_path = run_dir.expanduser().resolve() / ".internal" / "loop-state.json"
    payload = _load_json(state_path)
    if not isinstance(payload, dict):
        raise ValueError("loop-state.json must contain an object")
    history = payload.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("loop-state.json history must be a list")
    history.append({"at": _now_iso(), "stage": stage, "event": event})
    payload["status"] = status
    payload["stage"] = stage
    if stop_reason is not None:
        payload["stop_reason"] = stop_reason
    _write_json(state_path, payload)
    return LoopState.model_validate(payload)


def resume_run(run_dir: Path) -> LoopState:
    state = load_state(run_dir)
    if state.status == SUCCESS_STATUS or state.status in HONEST_STOP_STATUSES:
        raise ValueError(f"terminal run {state.run_id!r} cannot be resumed from {state.status}")
    return update_loop_state(
        run_dir,
        status="RUNNING",
        stage=state.stage,
        stop_reason="",
        event="run_resumed",
    )


def _parse_model(path: Path, model: type[BaseModel], errors: list[str]) -> BaseModel | None:
    try:
        return model.model_validate(_load_json(path))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        errors.append(f"{path.name}: {exc}")
        return None


def _artifact_has_run_id(path: Path, run_id: str, errors: list[str]) -> None:
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.name}: {exc}")
        return
    if not isinstance(payload, dict) or payload.get("run_id") != run_id:
        errors.append(f"{path.name}: run_id must equal {run_id!r}")


def validate_run(run_dir: Path) -> ValidationReport:
    run_dir = run_dir.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    state_path = run_dir / ".internal" / "loop-state.json"
    state_model = _parse_model(state_path, LoopState, errors)
    if not isinstance(state_model, LoopState):
        return ValidationReport(
            run_dir=str(run_dir),
            status="INVALID_OUTPUT",
            valid=False,
            errors=tuple(errors),
        )
    state = state_model
    if state.iteration > state.max_iterations:
        errors.append("loop-state.json: iteration exceeds max_iterations")

    evidence_path = run_dir / ".internal" / "evidence-manifest.json"
    if not evidence_path.is_file():
        errors.append("missing .internal/evidence-manifest.json")
    else:
        try:
            evidence = _load_json(evidence_path)
            core_paths = {record.get("path") for record in evidence.get("core", [])}
            missing_core = set(CORE_EVIDENCE_PATHS) - core_paths
            if missing_core:
                errors.append(f"evidence manifest omits core paths: {sorted(missing_core)}")
            unavailable_core = [
                record.get("path")
                for record in evidence.get("core", [])
                if not record.get("exists")
            ]
            if unavailable_core:
                errors.append(f"required evidence files are unavailable: {unavailable_core}")
            if evidence.get("freshness", {}).get("external_snapshot_status") != "CURRENT":
                warnings.append("external Instagram/competitor evidence is missing or stale")
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"evidence-manifest.json: {exc}")

    if state.status in HONEST_STOP_STATUSES:
        if not state.stop_reason.strip():
            errors.append("honest stop state requires a concrete stop_reason")
        if state.final_candidate_id:
            errors.append("honest stop state must not expose a final candidate")
        for relative in REQUIRED_STOP_ARTIFACTS:
            if not (run_dir / relative).is_file():
                errors.append(f"honest stop is missing {relative}")
        return ValidationReport(
            run_dir=str(run_dir),
            status=state.status,
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    if state.status != SUCCESS_STATUS:
        errors.append(
            f"loop-state.json: status must be {SUCCESS_STATUS} or an honest stop, got {state.status!r}"
        )
        return ValidationReport(
            run_dir=str(run_dir),
            status="INVALID_OUTPUT",
            valid=False,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    if state.stage != "CONCEPT_LOCK":
        errors.append("successful loop must stop at CONCEPT_LOCK")
    if not state.final_candidate_id:
        errors.append("successful loop requires final_candidate_id")

    for relative in REQUIRED_SUCCESS_ARTIFACTS:
        if not (run_dir / relative).is_file():
            errors.append(f"missing {relative}")
    if errors:
        return ValidationReport(
            run_dir=str(run_dir),
            status="INVALID_OUTPUT",
            valid=False,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    pool_path = run_dir / "concept-routes.json"
    pool_model = _parse_model(pool_path, CandidatePool, errors)
    verification_path = run_dir / "verification.json"
    verification_model = _parse_model(verification_path, VerificationBundle, errors)
    selection_path = run_dir / "concept-selection.json"
    selection_model = _parse_model(selection_path, ConceptSelection, errors)
    if not all(
        (
            isinstance(pool_model, CandidatePool),
            isinstance(verification_model, VerificationBundle),
            isinstance(selection_model, ConceptSelection),
        )
    ):
        return ValidationReport(
            run_dir=str(run_dir),
            status="INVALID_OUTPUT",
            valid=False,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    pool = pool_model
    verification = verification_model
    selection = selection_model
    per_iteration_counts: dict[int, int] = {}
    for candidate in pool.candidates:
        per_iteration_counts[candidate.iteration] = per_iteration_counts.get(candidate.iteration, 0) + 1
        if candidate.iteration > state.iteration:
            errors.append(
                f"candidate {candidate.candidate_id}: iteration exceeds loop-state iteration"
            )
    over_budget = {
        iteration: count
        for iteration, count in per_iteration_counts.items()
        if count > state.candidate_budget
    }
    if over_budget:
        errors.append(f"candidate budget exceeded by iteration: {over_budget}")
    for artifact_name, artifact_run_id in (
        ("concept-routes.json", pool.run_id),
        ("verification.json", verification.run_id),
        ("concept-selection.json", selection.run_id),
    ):
        if artifact_run_id != state.run_id:
            errors.append(f"{artifact_name}: run_id must match loop state")
    for relative in (
        "source-memory-brief.json",
        "concept-debate.json",
        "concept-repairs.json",
        "taste-gate.json",
    ):
        _artifact_has_run_id(run_dir / relative, state.run_id, errors)

    selected_id = state.final_candidate_id
    if selection.status != SUCCESS_STATUS:
        errors.append("concept-selection.json: status must be READY_FOR_CONCEPT_LOCK")
    if selection.selected_candidate_id != selected_id:
        errors.append("concept-selection.json: selected candidate must match loop state")
    if verification.selector.verdict != "PASS":
        errors.append("verification.json: selector verdict must be PASS")
    if verification.selector.candidate_id != selected_id:
        errors.append("verification.json: selected candidate must match loop state")
    if selection.selector_task_id != verification.selector.selector_task_id:
        errors.append("selector task ID must match across selection and verification")

    raw_pool = _load_json(pool_path)
    raw_candidates = {
        str(candidate.get("candidate_id")): candidate
        for candidate in raw_pool.get("candidates", [])
        if isinstance(candidate, dict) and candidate.get("candidate_id")
    }
    selected_raw = raw_candidates.get(str(selected_id))
    selected_model = next(
        (candidate for candidate in pool.candidates if candidate.candidate_id == selected_id),
        None,
    )
    if selected_raw is None or selected_model is None:
        errors.append("selected candidate is missing from concept-routes.json")
    else:
        expected_hash = candidate_fingerprint(selected_raw)
        expected_blind_hash = blind_candidate_fingerprint(selected_raw)
        selected_reviews = [
            review for review in verification.reviews if review.candidate_id == selected_id
        ]
        verifier_tasks = {review.verifier_task_id for review in selected_reviews}
        if len(selected_reviews) < 2 or len(verifier_tasks) < 2:
            errors.append("selected candidate requires two distinct blind verifier passes")
        for review in selected_reviews:
            if review.candidate_sha256 != expected_hash:
                errors.append(
                    f"verification {review.verifier_task_id}: candidate fingerprint is stale"
                )
            if review.blind_input_sha256 != expected_blind_hash:
                errors.append(
                    f"verification {review.verifier_task_id}: blind input fingerprint is stale"
                )
            if review.maker_task_id != selected_model.maker_task_id:
                errors.append(
                    f"verification {review.verifier_task_id}: maker provenance mismatch"
                )
            if review.verdict != "PASS" or not review.satisfies_completion:
                errors.append(
                    f"verification {review.verifier_task_id}: selected route did not earn PASS"
                )
        if verification.selector.candidate_sha256 != expected_hash:
            errors.append("selector candidate fingerprint is stale")
        if verification.selector.selector_task_id == selected_model.maker_task_id:
            errors.append("fresh selector cannot be the selected route's maker")
        if verification.selector.selector_task_id in verifier_tasks:
            errors.append("fresh selector task must be distinct from blind verifier tasks")
        if set(verification.selector.critic_task_ids) != verifier_tasks:
            errors.append("selector critic_task_ids must match the selected route's verifier tasks")

    creator_brief = (run_dir / "creator-brief.md").read_text(encoding="utf-8")
    if selected_id and selected_id not in creator_brief:
        errors.append("creator-brief.md must name the selected candidate ID")
    for candidate in pool.candidates:
        if candidate.candidate_id != selected_id and candidate.candidate_id in creator_brief:
            errors.append("creator-brief.md exposes a non-selected route")
    lowered_brief = creator_brief.lower()
    if "guaranteed to go viral" in lowered_brief or "will go viral" in lowered_brief:
        errors.append("creator-brief.md must not promise virality")

    return ValidationReport(
        run_dir=str(run_dir),
        status=SUCCESS_STATUS if not errors else "INVALID_OUTPUT",
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def build_codex_command(
    *,
    codex_path: str,
    repo_root: Path,
    last_message_path: Path,
    live_search: bool,
) -> list[str]:
    command = [codex_path]
    if live_search:
        command.append("--search")
    command.extend(
        [
            "-a",
            "never",
            "exec",
            "--ephemeral",
            "-C",
            str(repo_root),
            "-s",
            "workspace-write",
            "-o",
            str(last_message_path),
            "-",
        ]
    )
    return command


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def execute_loop(
    repo_root: Path,
    run_dir: Path,
    *,
    config: IdeaLoopConfig,
    run_command: RunCommand = subprocess.run,
) -> tuple[int, ValidationReport]:
    repo_root = repo_root.resolve()
    run_dir = run_dir.resolve()
    internal = run_dir / ".internal"
    if not run_dir.is_relative_to(repo_root):
        report = ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=("Executable loop run directories must stay inside the repository.",),
        )
        _write_json(internal / "validation.json", report.to_dict())
        update_loop_state(
            run_dir,
            status="EXECUTION_FAILED",
            stage="EXECUTE",
            stop_reason=report.errors[0],
            event="execution_rejected_outside_repo",
        )
        return 2, report
    prompt = (internal / "orchestration-prompt.md").read_text(encoding="utf-8")
    executions_root = internal / "executions"
    execution_number = len(list(executions_root.glob("run-*"))) + 1
    execution_dir = executions_root / f"run-{execution_number:02d}"
    execution_dir.mkdir(parents=True, exist_ok=False)
    codex = shutil.which("codex")
    if not codex:
        report = ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=("Codex CLI is unavailable.",),
        )
        _write_json(internal / "validation.json", report.to_dict())
        update_loop_state(
            run_dir,
            status="EXECUTION_FAILED",
            stage="EXECUTE",
            stop_reason=report.errors[0],
            event="codex_cli_unavailable",
        )
        return 127, report

    command = build_codex_command(
        codex_path=codex,
        repo_root=repo_root,
        last_message_path=execution_dir / "codex-last-message.md",
        live_search=config.live_search,
    )
    try:
        completed = run_command(
            command,
            cwd=repo_root,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=config.command_timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        report = ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=(str(exc),),
        )
        _write_json(internal / "validation.json", report.to_dict())
        update_loop_state(
            run_dir,
            status="EXECUTION_FAILED",
            stage="EXECUTE",
            stop_reason=report.errors[0],
            event="codex_execution_exception",
        )
        return 124, report

    (execution_dir / "codex-stdout.log").write_text(completed.stdout, encoding="utf-8")
    (execution_dir / "codex-stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        report = ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=(f"Codex exited with status {completed.returncode}.",),
        )
        _write_json(internal / "validation.json", report.to_dict())
        update_loop_state(
            run_dir,
            status="EXECUTION_FAILED",
            stage="EXECUTE",
            stop_reason=report.errors[0],
            event="codex_nonzero_exit",
        )
        return completed.returncode, report

    report = validate_run(run_dir)
    _write_json(internal / "validation.json", report.to_dict())
    if report.valid and report.status == SUCCESS_STATUS:
        return 0, report
    if report.valid and report.status in HONEST_STOP_STATUSES:
        return 3, report
    update_loop_state(
        run_dir,
        status="INVALID_OUTPUT",
        stage="VALIDATE",
        stop_reason="; ".join(report.errors[:5]),
        event="completion_contract_failed",
    )
    return 2, report


def load_state(run_dir: Path) -> LoopState:
    return LoopState.model_validate(
        _load_json(run_dir.expanduser().resolve() / ".internal" / "loop-state.json")
    )


def find_candidate(candidate_file: Path, candidate_id: str) -> dict[str, Any]:
    payload = _load_json(candidate_file)
    if not isinstance(payload, dict):
        raise ValueError("candidate file must contain a JSON object")
    for candidate in payload.get("candidates", []):
        if isinstance(candidate, dict) and candidate.get("candidate_id") == candidate_id:
            return candidate
    raise ValueError(f"candidate {candidate_id!r} was not found")
