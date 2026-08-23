"""Bounded maker/checker loop for one evidence-backed Instagram idea.

The module owns deterministic loop state, evidence fingerprints, completion
validation, and the Codex CLI boundary. Creative invention and editorial
judgment remain with distinct read-only subagents. The successful terminal
state is ``READY_FOR_CONCEPT_LOCK``; publishing is deliberately out of scope.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, Iterator, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


SCHEMA_VERSION = "1.0"
SUCCESS_STATUS = "READY_FOR_CONCEPT_LOCK"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
IDEA_LOOP_OUTPUT_ROOT = Path("output/idea-loops")
EXECUTION_LEASE_PATH = Path(".internal/execution-lease.json")
FINALIZATION_DIRECTORY = ".finalizations"
DATE_PART = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TaskId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]
ArtifactId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]
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
    "corpus/posts/**/*",
    "corpus/reels/**/*",
    "corpus/forensic-instagram/**/*",
    "corpus/competitors/**/*",
    "output/concepts/**/concept.json",
    "output/concepts/**/concept-selection.json",
    "output/carousels/**/concept.json",
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

REQUIRED_CREATOR_BRIEF_HEADINGS = (
    "## Concrete moment",
    "## Why a cold viewer recognizes it",
    "## Format and visible proof",
    "## One-person send reason",
    "## Evidence and uncertainties",
    "## Decision needed",
)

REQUIRED_STOP_BASE_ARTIFACTS = (
    "source-memory-brief.json",
    "creator-brief.md",
)

REQUIRED_EVALUATED_STOP_ARTIFACTS = (
    "concept-routes.json",
    "verification.json",
)

EVIDENCE_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".tsv", ".txt"}
MAX_EVIDENCE_FILE_BYTES = 5 * 1024 * 1024
MAX_CODEX_EVENT_BYTES = 20 * 1024 * 1024
MAX_CODEX_STDERR_BYTES = 2 * 1024 * 1024
FUTURE_EVIDENCE_TOLERANCE = timedelta(days=1)
IDEA_AGENT_ROLES = {
    "asot_idea_scout",
    "asot_idea_maker",
    "asot_idea_verifier",
}
IDEA_AGENT_ROLE_MARKER = re.compile(
    r"^ASOT_IDEA_LOOP_ROLE=(asot_idea_scout|asot_idea_maker|asot_idea_verifier)$"
)
IDEA_AGENT_ASSIGNMENT_MARKER = re.compile(
    r"^ASOT_IDEA_LOOP_ASSIGNMENT_SHA256=([0-9a-f]{64})$"
)
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SUPPORTING_EVIDENCE_PURPOSES: set[str | None] = {
    None,
    "owned_account_signal",
    "external_or_report_signal",
}
COLLISION_EVIDENCE_PURPOSES: set[str | None] = {"collision_check_only"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.urandom(12).hex()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(
        path,
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    )


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _unsafe_run_entry(run_dir: Path) -> str | None:
    """Reject links, special files, and multiply linked files in agent output."""

    try:
        root_metadata = run_dir.lstat()
    except OSError as exc:
        return f"cannot inspect run directory {run_dir}: {exc}"
    if stat.S_ISLNK(root_metadata.st_mode):
        return f"run directory itself is a forbidden symlink: {run_dir}"
    if not run_dir.is_dir():
        return f"run directory is not a directory: {run_dir}"
    for directory, dirnames, filenames in os.walk(run_dir, followlinks=False):
        parent = Path(directory)
        for name in [*dirnames, *filenames]:
            path = parent / name
            try:
                metadata = path.lstat()
            except OSError as exc:
                return f"cannot inspect run entry {path}: {exc}"
            relative = path.relative_to(run_dir)
            if stat.S_ISLNK(metadata.st_mode):
                return f"run output contains a forbidden symlink: {relative}"
            if name in dirnames and not stat.S_ISDIR(metadata.st_mode):
                return f"run output contains a non-directory ancestor: {relative}"
            if name in filenames:
                if not stat.S_ISREG(metadata.st_mode):
                    return f"run output contains a forbidden special file: {relative}"
                if metadata.st_nlink != 1:
                    return f"run output contains a multiply linked file: {relative}"
    return None


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_regular_file(path: Path) -> str:
    """Hash one regular, singly linked file without following a final symlink."""

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError(f"refusing to hash unsafe run file: {path}")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _run_file_hashes(
    run_dir: Path,
    *,
    exclude: set[str] | None = None,
) -> dict[str, str]:
    """Return the deterministic file manifest for one safe run tree."""

    resolved = run_dir.expanduser().resolve()
    unsafe_entry = _unsafe_run_entry(resolved)
    if unsafe_entry:
        raise ValueError(unsafe_entry)
    excluded = exclude or set()
    hashes: dict[str, str] = {}
    for path in sorted(resolved.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(resolved).as_posix()
        if relative in excluded:
            continue
        hashes[relative] = _sha256_regular_file(path)
    return hashes


def _file_manifest_sha256(hashes: dict[str, str]) -> str:
    payload = json.dumps(
        sorted(hashes.items()),
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _relative(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _source_date(path: Path) -> datetime | None:
    """Prefer a source's dated path over mutable filesystem metadata."""

    for part in reversed(path.parts):
        if not DATE_PART.fullmatch(part):
            continue
        try:
            return datetime.strptime(part, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


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
    """Project a candidate onto the exact author-hidden critic allowlist."""

    visible = (
        "candidate_id",
        "alive_premise",
        "moment_origin",
        "moment_origin_detail",
        "moment_origin_path",
        "lived_fact_status",
        "title",
        "concrete_moment",
        "universal_truth",
        "audience_mirror",
        "scroll_stop",
        "emotional_contradiction",
        "scene_proof",
        "relationship_motion",
        "retention_ladder",
        "payoff",
        "dm_send_reason",
        "format_recommendation",
        "asot_turn",
        "evidence_paths",
        "collision_paths",
        "novelty_fingerprint",
        "risks",
    )
    return {key: candidate[key] for key in visible if key in candidate}


def blind_candidate_fingerprint(candidate: dict[str, Any]) -> str:
    return candidate_fingerprint(blind_candidate_card(candidate))


def failure_signature(payload: dict[str, Any]) -> str:
    """Hash stable failure categories while ignoring candidate/task churn."""

    normalized_reviews: list[dict[str, Any]] = []
    for raw_review in payload.get("reviews", []):
        if not isinstance(raw_review, dict):
            continue
        scores = raw_review.get("scores", {}) if isinstance(raw_review.get("scores"), dict) else {}
        director = (
            scores.get("story_director", {})
            if isinstance(scores.get("story_director"), dict)
            else {}
        )
        threshold_failures: list[str] = []
        for key, threshold in (
            ("story_selling", 28),
            ("golden_theme", 28),
            ("distribution", 26),
            ("visual_generativity", 27),
        ):
            value = scores.get(key)
            if not isinstance(value, int) or value < threshold:
                threshold_failures.append(key)
        director_failures = sorted(
            key
            for key in ("hook", "story", "bridge", "relationship_motion", "ending", "dm_send")
            if not isinstance(director.get(key), int) or director[key] < 8
        )
        normalized_reviews.append(
            {
                "threshold_failures": sorted(threshold_failures),
                "director_failures": director_failures,
                "stage_scene_gate": raw_review.get("stage_scene_gate"),
                "taste_gate": raw_review.get("taste_gate"),
                "safety_gate": raw_review.get("safety_gate"),
                # Free-form labels are deliberately collapsed. Otherwise a
                # controller could evade stagnation by renaming the same
                # exclusion or hard failure on every round.
                "has_exclusion": bool(raw_review.get("exclusion_hits")),
                "has_hard_failure": bool(raw_review.get("hard_failures")),
            }
        )
    normalized_reviews.sort(key=lambda item: json.dumps(item, sort_keys=True))
    return candidate_fingerprint({"failures": normalized_reviews})


def _evidence_record(repo_root: Path, path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    inside_repo = resolved.is_relative_to(repo_root.resolve())
    record: dict[str, Any] = {
        "path": _relative(repo_root, path),
        "exists": path.is_file() and inside_repo,
    }
    if path.is_file() and not inside_repo:
        record["rejected_reason"] = "resolved path escapes repo root"
    if not path.is_file():
        return record
    if not inside_repo:
        return record
    stat = path.stat()
    source_date = _source_date(path)
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
    if source_date is not None:
        record["source_date"] = source_date.date().isoformat()
    return record


def build_evidence_manifest(
    repo_root: Path,
    *,
    run_id: str | None = None,
    dynamic_limit: int = 40,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Snapshot the files agents may inspect without embedding their contents."""

    repo_root = repo_root.resolve()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    core = [_evidence_record(repo_root, repo_root / relative) for relative in CORE_EVIDENCE_PATHS]

    dynamic_paths: dict[str, Path] = {}
    for pattern in DYNAMIC_EVIDENCE_GLOBS:
        for path in repo_root.glob(pattern):
            if (
                path.is_file()
                and path.resolve().is_relative_to(repo_root)
                and path.suffix.lower() in EVIDENCE_SUFFIXES
                and path.stat().st_size <= MAX_EVIDENCE_FILE_BYTES
            ):
                dynamic_paths[_relative(repo_root, path)] = path
    ranked_dynamic = sorted(
        dynamic_paths.values(),
        key=lambda path: (
            _source_date(path).timestamp() if _source_date(path) else path.stat().st_mtime,
            str(path),
        ),
        reverse=True,
    )
    ranked_external = [
        path
        for path in ranked_dynamic
        if _relative(repo_root, path).startswith(
            ("corpus/forensic-instagram/", "corpus/competitors/")
        )
    ]
    reserved_external = ranked_external[: min(10, dynamic_limit)]
    newest_dynamic = reserved_external + [
        path for path in ranked_dynamic if path not in reserved_external
    ][: max(0, dynamic_limit - len(reserved_external))]
    dynamic = [_evidence_record(repo_root, path) for path in newest_dynamic]
    for record in dynamic:
        reference = str(record["path"])
        if reference.startswith(("output/concepts/", "output/carousels/")):
            record["purpose"] = "collision_check_only"
        elif reference.startswith(("corpus/posts/", "corpus/reels/")):
            record["purpose"] = "owned_account_signal"
        else:
            record["purpose"] = "external_or_report_signal"

    external_records = [
        record
        for record in dynamic
        if str(record["path"]).startswith(("corpus/forensic-instagram/", "corpus/competitors/"))
    ]
    newest_external_at: datetime | None = None
    for record in external_records:
        evidence_at = record.get("source_date") or record.get("modified_at")
        if not evidence_at:
            continue
        parsed = datetime.fromisoformat(str(evidence_at))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        newest_external_at = max(newest_external_at, parsed) if newest_external_at else parsed

    if newest_external_at is None:
        external_status = "MISSING"
        external_age_days = None
    elif newest_external_at > now + FUTURE_EVIDENCE_TOLERANCE:
        external_status = "FUTURE"
        external_age_days = (now - newest_external_at).days
    else:
        external_age_days = (now - newest_external_at).days
        external_status = "CURRENT" if external_age_days <= 30 else "STALE"

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
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

    candidate_id: ArtifactId
    iteration: int = Field(ge=1)
    maker_agent: Literal["asot_idea_maker"]
    maker_task_id: TaskId
    parent_candidate_id: ArtifactId | None = None
    repair_task_id: TaskId | None = None
    alive_premise: str = Field(min_length=1)
    moment_origin: Literal[
        "creator_seed",
        "documented_repo_story",
        "generic_relationship_hypothesis",
    ]
    moment_origin_detail: str = Field(min_length=1)
    moment_origin_path: str | None = None
    lived_fact_status: Literal[
        "CONFIRMED",
        "NOT_CLAIMED",
        "CREATOR_CONFIRMATION_REQUIRED",
    ]
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
    collision_paths: list[str] = Field(default_factory=list)
    novelty_fingerprint: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def repaired_routes_keep_lineage(self) -> "IdeaCandidate":
        if self.iteration > 1 and not (self.parent_candidate_id and self.repair_task_id):
            raise ValueError("iteration > 1 requires parent_candidate_id and repair_task_id")
        if (
            self.moment_origin == "generic_relationship_hypothesis"
            and self.lived_fact_status == "CONFIRMED"
        ):
            raise ValueError("a generic relationship hypothesis cannot claim a confirmed lived fact")
        if self.moment_origin == "documented_repo_story" and not self.moment_origin_path:
            raise ValueError("a documented repo story requires moment_origin_path")
        if self.moment_origin != "documented_repo_story" and self.moment_origin_path:
            raise ValueError(
                "moment_origin_path is only valid for a documented repo story"
            )
        return self


class CandidatePool(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    candidates: list[IdeaCandidate] = Field(min_length=1)

    @model_validator(mode="after")
    def candidate_ids_are_unique(self) -> "CandidatePool":
        candidate_ids = [candidate.candidate_id for candidate in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate IDs must be unique")
        return self


class SourceMemoryBrief(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    scout_agent: Literal["asot_idea_scout"]
    scout_task_id: TaskId
    evidence_paths: list[str] = Field(min_length=1)
    collision_paths: list[str] = Field(default_factory=list)
    excluded_lanes: list[str] = Field(default_factory=list)
    opportunity_signals: list[str] = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)


class BlindDebateRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: ArtifactId
    blind_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    critic_task_ids: list[TaskId] = Field(min_length=2)
    objections: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def critics_are_distinct(self) -> "BlindDebateRecord":
        if len(set(self.critic_task_ids)) < 2:
            raise ValueError("blind debate requires two distinct critic tasks")
        return self


class ConceptDebate(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    blind_reviews: list[BlindDebateRecord] = Field(min_length=1)


class ConceptRepairRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: ArtifactId
    parent_candidate_id: ArtifactId
    repair_task_id: TaskId
    feedback_task_ids: list[TaskId] = Field(min_length=1)
    changes: list[str] = Field(min_length=1)


class ConceptRepairs(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    repairs: list[ConceptRepairRecord] = Field(default_factory=list)


class TasteGateRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: ArtifactId
    verifier_task_ids: list[TaskId] = Field(min_length=2)
    verdict: Literal["PASS_NO_CAP", "REPAIR", "STOP"]
    reasons: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def verifiers_are_distinct(self) -> "TasteGateRecord":
        if len(set(self.verifier_task_ids)) < 2:
            raise ValueError("taste gate requires two distinct verifier tasks")
        return self


class TasteGateBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    records: list[TasteGateRecord] = Field(min_length=1)
    selected_candidate_id: str | None = None


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

    candidate_id: ArtifactId
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    blind_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    maker_task_id: TaskId
    verifier_agent: Literal["asot_idea_verifier"]
    verifier_task_id: TaskId
    verifier_lens: Literal[
        "audience_distribution",
        "stage_scene_taste_safety",
    ]
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
    selector_task_id: TaskId
    candidate_id: ArtifactId | None = None
    candidate_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    critic_task_ids: list[TaskId] = Field(min_length=2)
    verdict: Literal["PASS", "NO_GO"]
    reasons: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def selection_shape_matches_verdict(self) -> "SelectorRecord":
        if len(set(self.critic_task_ids)) < 2:
            raise ValueError("selector requires two distinct critic tasks")
        if self.verdict == "PASS" and not (self.candidate_id and self.candidate_sha256):
            raise ValueError("PASS selector requires a candidate ID and fingerprint")
        if self.verdict == "NO_GO" and (self.candidate_id or self.candidate_sha256):
            raise ValueError("NO_GO selector must not promote a candidate")
        return self


class VerificationBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    reviews: list[VerificationRecord] = Field(min_length=1)
    selector: SelectorRecord


class CriticInputRecord(BaseModel):
    """Exact blind card persisted before a critic result can count."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    iteration: int = Field(ge=1)
    verifier_task_id: TaskId
    verifier_lens: Literal[
        "audience_distribution",
        "stage_scene_taste_safety",
    ]
    candidate_id: ArtifactId
    blind_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    card: dict[str, Any]


class AgentResultArtifact(BaseModel):
    """One task-produced payload before controller-owned task IDs are injected."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "source_memory_brief",
        "candidate",
        "verification_record",
        "selector_record",
    ]
    payload: dict[str, Any]


class AgentResultEnvelope(BaseModel):
    """Strict terminal message emitted by an independently spawned task."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    agent_name: Literal[
        "asot_idea_scout",
        "asot_idea_maker",
        "asot_idea_verifier",
    ]
    artifacts: list[AgentResultArtifact] = Field(min_length=1)


class StopEvidence(BaseModel):
    """Structured proof for an early stop before candidate evaluation is safe."""

    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    status: Literal["STALE_EVIDENCE", "HUMAN_REQUIRED"]
    reason: str = Field(min_length=1)
    evidence_paths: list[str] = Field(min_length=1)
    missing_or_ambiguous_inputs: list[str] = Field(min_length=1)


class ConceptSelection(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    selected_candidate_id: str | None = None
    selector_task_id: TaskId
    creator_approval: Literal["PENDING"] = "PENDING"
    reason: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    uncertainties: list[str] = Field(default_factory=list)


def artifact_schema() -> dict[str, Any]:
    """Expose the exact agent-written JSON contract without duplicating it in prompts."""

    return {
        "schema_version": SCHEMA_VERSION,
        "loop_state": LoopState.model_json_schema(),
        "source_memory_brief": SourceMemoryBrief.model_json_schema(),
        "concept_routes": CandidatePool.model_json_schema(),
        "concept_debate": ConceptDebate.model_json_schema(),
        "concept_repairs": ConceptRepairs.model_json_schema(),
        "taste_gate": TasteGateBundle.model_json_schema(),
        "verification": VerificationBundle.model_json_schema(),
        "critic_input": CriticInputRecord.model_json_schema(),
        "agent_result_envelope": AgentResultEnvelope.model_json_schema(),
        "stop_evidence": StopEvidence.model_json_schema(),
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
        if self.live_search:
            raise ValueError(
                "live_search is disabled until web results have a durable "
                "URL/date/source provenance ledger"
            )


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


@dataclass(frozen=True)
class _ExecutionExpectations:
    repo_root: Path
    evidence_manifest_sha256: str
    run_id: str
    max_iterations: int
    candidate_budget: int
    execution_event_hashes: tuple[tuple[str, str], ...]
    initial_state: LoopState


def allocate_run_dir(
    repo_root: Path,
    *,
    requested: Path | None = None,
    now: datetime | None = None,
) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    output_error = output_root_error(repo_root)
    if output_error:
        raise ValueError(output_error)
    now = now or datetime.now().astimezone()
    base = repo_root / "output" / "idea-loops" / now.strftime("%Y-%m-%d")
    stem = now.strftime("run-%H%M%S")
    candidate = base / stem
    suffix = 2
    while candidate.exists():
        candidate = base / f"{stem}-{suffix}"
        suffix += 1
    return candidate.resolve()


def output_root_error(repo_root: Path) -> str | None:
    repo_root = repo_root.expanduser().resolve()
    output_root = repo_root / IDEA_LOOP_OUTPUT_ROOT
    current = repo_root
    for part in IDEA_LOOP_OUTPUT_ROOT.parts:
        current = current / part
        if current.is_symlink():
            return f"Idea-loop output boundary contains a symlink: {current}."
    if output_root.exists() and not output_root.is_dir():
        return f"Idea-loop output root is not a directory: {output_root}."
    if output_root.resolve().parent.parent != repo_root:
        return f"Idea-loop output root escapes the repository: {output_root}."
    return None


def execution_location_error(repo_root: Path, run_dir: Path) -> str | None:
    """Return why a live run is outside the exact durable output boundary."""

    repo_root = repo_root.expanduser().resolve()
    run_dir = run_dir.expanduser().resolve()
    boundary_error = output_root_error(repo_root)
    if boundary_error:
        return boundary_error
    lexical_output_root = repo_root / IDEA_LOOP_OUTPUT_ROOT
    unresolved_run = run_dir.expanduser().absolute()
    current = lexical_output_root
    try:
        unresolved_relative = unresolved_run.relative_to(lexical_output_root)
    except ValueError:
        unresolved_relative = None
    if unresolved_relative is not None:
        for part in unresolved_relative.parts:
            current = current / part
            if current.is_symlink():
                return f"Live run boundary contains a symlink: {current}."
    output_root = lexical_output_root.resolve()
    try:
        relative = run_dir.relative_to(output_root)
    except ValueError:
        return f"Live runs must stay under {output_root}."
    if len(relative.parts) != 2 or not DATE_PART.fullmatch(relative.parts[0]):
        return (
            "Live runs must use output/idea-loops/YYYY-MM-DD/<run-id>; "
            f"got {run_dir}."
        )
    try:
        datetime.strptime(relative.parts[0], "%Y-%m-%d")
    except ValueError:
        return f"Live run directory has an invalid calendar date: {relative.parts[0]}."
    return None


def _lease_path(run_dir: Path) -> Path:
    resolved = run_dir.expanduser().resolve()
    if (
        resolved.parent.parent.name == IDEA_LOOP_OUTPUT_ROOT.name
        and DATE_PART.fullmatch(resolved.parent.name)
    ):
        lease_name = _sha256_bytes(str(resolved).encode("utf-8")) + ".json"
        return resolved.parent.parent / ".leases" / lease_name
    return resolved / EXECUTION_LEASE_PATH


def _finalization_record_name(run_dir: Path) -> str:
    resolved = run_dir.expanduser().resolve()
    return _sha256_bytes(str(resolved).encode("utf-8")) + ".json"


def _open_controller_sibling_directory(
    run_dir: Path,
    *,
    directory_name: str,
    create: bool,
) -> tuple[int, int]:
    """Open a controller-only sibling directory without following symlinks."""

    resolved = run_dir.expanduser().resolve()
    output_root = resolved.parent.parent
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    root_descriptor = os.open(output_root, directory_flags)
    try:
        if create:
            try:
                os.mkdir(directory_name, 0o700, dir_fd=root_descriptor)
            except FileExistsError:
                pass
        directory_descriptor = os.open(
            directory_name,
            directory_flags,
            dir_fd=root_descriptor,
        )
    except BaseException:
        os.close(root_descriptor)
        raise
    return root_descriptor, directory_descriptor


def _read_controller_finalization(run_dir: Path) -> dict[str, Any] | None:
    try:
        root_descriptor, directory_descriptor = _open_controller_sibling_directory(
            run_dir,
            directory_name=FINALIZATION_DIRECTORY,
            create=False,
        )
    except OSError:
        return None
    try:
        read_flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            read_flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(
                _finalization_record_name(run_dir),
                read_flags,
                dir_fd=directory_descriptor,
            )
        except OSError:
            return None
        try:
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None
    finally:
        os.close(directory_descriptor)
        os.close(root_descriptor)


def controller_finalization_valid(run_dir: Path, state: LoopState | None = None) -> bool:
    """Return whether the unsandboxed controller finalized the exact state."""

    resolved = run_dir.expanduser().resolve()
    if state is None:
        try:
            state = load_state(resolved)
        except (OSError, json.JSONDecodeError, ValidationError):
            return False
    payload = _read_controller_finalization(resolved)
    if payload is None:
        return False
    state_path = resolved / ".internal" / "loop-state.json"
    try:
        state_hash = _sha256_file(state_path)
    except OSError:
        return False
    return (
        payload.get("schema_version") == SCHEMA_VERSION
        and payload.get("run_id") == state.run_id
        and payload.get("status") == state.status
        and payload.get("state_sha256") == state_hash
        and payload.get("valid") is True
    )


def _write_controller_finalization(
    run_dir: Path,
    report: ValidationReport,
) -> None:
    resolved = run_dir.expanduser().resolve()
    state = load_state(resolved)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": state.run_id,
        "status": report.status,
        "valid": report.valid,
        "state_sha256": _sha256_file(resolved / ".internal" / "loop-state.json"),
        "finalized_at": _now_iso(),
    }
    root_descriptor, directory_descriptor = _open_controller_sibling_directory(
        resolved,
        directory_name=FINALIZATION_DIRECTORY,
        create=True,
    )
    temporary_name = f".{_finalization_record_name(resolved)}.{os.urandom(8).hex()}.tmp"
    final_name = _finalization_record_name(resolved)
    create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        create_flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(
            temporary_name,
            create_flags,
            0o600,
            dir_fd=directory_descriptor,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(
                temporary_name,
                final_name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
            )
        finally:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
            except FileNotFoundError:
                pass
    finally:
        os.close(directory_descriptor)
        os.close(root_descriptor)


def _capture_execution_expectations(
    repo_root: Path,
    run_dir: Path,
    *,
    config: IdeaLoopConfig,
) -> _ExecutionExpectations:
    """Capture controller-owned values before the child can write to the run."""

    expected_repo_root = repo_root.expanduser().resolve()
    evidence_path = run_dir / ".internal" / "evidence-manifest.json"
    try:
        evidence_bytes = evidence_path.read_bytes()
        manifest = json.loads(evidence_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot capture evidence manifest before execution: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("cannot execute: evidence manifest must contain an object")
    raw_repo_root = manifest.get("repo_root")
    if not isinstance(raw_repo_root, str) or not Path(raw_repo_root).is_absolute():
        raise ValueError("cannot execute: evidence manifest repo_root must be absolute")
    manifest_repo_root = Path(raw_repo_root).expanduser().resolve()
    if manifest_repo_root != expected_repo_root:
        raise ValueError(
            "cannot execute: evidence manifest repo_root does not match the "
            f"controller repo_root ({manifest_repo_root} != {expected_repo_root})"
        )

    state = load_state(run_dir)
    if (
        state.max_iterations != config.max_iterations
        or state.candidate_budget != config.candidate_budget
    ):
        raise ValueError(
            "cannot execute: loop-state budgets do not match the controller configuration"
        )
    event_hashes = tuple(
        (
            str(path.relative_to(run_dir)),
            _sha256_file(path),
        )
        for path in sorted(
            (run_dir / ".internal" / "executions").glob("run-*/codex-events.jsonl")
        )
        if path.is_file()
    )
    return _ExecutionExpectations(
        repo_root=expected_repo_root,
        evidence_manifest_sha256=_sha256_bytes(evidence_bytes),
        run_id=state.run_id,
        max_iterations=state.max_iterations,
        candidate_budget=state.candidate_budget,
        execution_event_hashes=event_hashes,
        initial_state=state,
    )


def _execution_integrity_errors(
    run_dir: Path,
    expectations: _ExecutionExpectations,
) -> list[str]:
    """Reject child mutations to controller-owned evidence and loop identity."""

    errors: list[str] = []
    evidence_path = run_dir / ".internal" / "evidence-manifest.json"
    try:
        evidence_bytes = evidence_path.read_bytes()
    except OSError as exc:
        errors.append(f"evidence manifest unavailable after controller return: {exc}")
    else:
        if _sha256_bytes(evidence_bytes) != expectations.evidence_manifest_sha256:
            errors.append(
                "evidence-manifest.json changed after the controller captured "
                "its pre-execution snapshot"
            )
        try:
            manifest = json.loads(evidence_bytes)
        except json.JSONDecodeError as exc:
            errors.append(f"evidence-manifest.json is invalid after controller return: {exc}")
        else:
            raw_repo_root = manifest.get("repo_root") if isinstance(manifest, dict) else None
            if not isinstance(raw_repo_root, str) or not Path(raw_repo_root).is_absolute():
                errors.append(
                    "evidence-manifest.json: repo_root is invalid after controller return"
                )
            elif Path(raw_repo_root).expanduser().resolve() != expectations.repo_root:
                errors.append(
                    "evidence-manifest.json: repo_root changed after controller capture"
                )

    state_path = run_dir / ".internal" / "loop-state.json"
    try:
        state_payload = _load_json(state_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"loop-state.json is unavailable after controller return: {exc}")
        return errors
    if not isinstance(state_payload, dict):
        errors.append("loop-state.json must remain an object after controller return")
        return errors

    protected_values = (
        ("run_id", expectations.run_id, str),
        ("max_iterations", expectations.max_iterations, int),
        ("candidate_budget", expectations.candidate_budget, int),
    )
    for field, expected, expected_type in protected_values:
        actual = state_payload.get(field)
        if type(actual) is not expected_type or actual != expected:
            errors.append(f"loop-state.json: {field} changed after controller capture")
    expected_seed = expectations.initial_state.seed
    if state_payload.get("seed") != expected_seed:
        errors.append("loop-state.json: seed changed after controller capture")

    for relative, expected_hash in expectations.execution_event_hashes:
        path = run_dir / relative
        try:
            current_hash = _sha256_file(path)
        except OSError as exc:
            errors.append(
                f"prior Codex event provenance changed after controller capture: "
                f"{relative}: {exc}"
            )
            continue
        if current_hash != expected_hash:
            errors.append(
                "prior Codex event provenance changed after controller capture: "
                f"{relative}"
            )
    return errors


def _mark_integrity_failure(
    run_dir: Path,
    expectations: _ExecutionExpectations,
    errors: tuple[str, ...],
) -> None:
    """Persist INVALID_OUTPUT while restoring protected controller values."""

    state_path = run_dir / ".internal" / "loop-state.json"
    try:
        payload = _load_json(state_path)
    except (OSError, json.JSONDecodeError):
        payload = expectations.initial_state.model_dump(mode="json")
    if not isinstance(payload, dict):
        payload = expectations.initial_state.model_dump(mode="json")
    history = payload.get("history")
    if not isinstance(history, list):
        history = list(expectations.initial_state.history)
    history.append(
        {
            "at": _now_iso(),
            "stage": "VALIDATE",
            "event": "controller_integrity_failed",
        }
    )
    payload.update(
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": expectations.run_id,
            "max_iterations": expectations.max_iterations,
            "candidate_budget": expectations.candidate_budget,
            "seed": expectations.initial_state.seed,
            "status": "INVALID_OUTPUT",
            "stage": "VALIDATE",
            "stop_reason": "; ".join(errors[:5]),
            "history": history,
        }
    )
    _write_json(state_path, payload)


@contextmanager
def execution_lease(run_dir: Path) -> Iterator[None]:
    """Hold an atomic lease without following a writable symlink ancestor."""

    lease_path = _lease_path(run_dir)
    lease_parent = lease_path.parent
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    parent_descriptor: int | None = None
    lease_directory_descriptor: int | None = None
    try:
        if lease_parent.name == ".leases":
            parent_descriptor = os.open(lease_parent.parent, directory_flags)
            try:
                os.mkdir(lease_parent.name, 0o700, dir_fd=parent_descriptor)
            except FileExistsError:
                pass
            lease_directory_descriptor = os.open(
                lease_parent.name,
                directory_flags,
                dir_fd=parent_descriptor,
            )
        else:
            lease_directory_descriptor = os.open(lease_parent, directory_flags)
    except OSError as exc:
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        raise ValueError(f"unsafe execution lease directory {lease_parent}: {exc}") from exc

    lease_id = _sha256_bytes(f"{os.getpid()}:{_now_iso()}:{run_dir}".encode("utf-8"))
    create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        create_flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(
            lease_path.name,
            create_flags,
            0o600,
            dir_fd=lease_directory_descriptor,
        )
    except FileExistsError as exc:
        os.close(lease_directory_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        raise ValueError(
            f"run already has an active execution lease: {lease_path}"
        ) from exc
    except OSError:
        os.close(lease_directory_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)
        raise
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema_version": SCHEMA_VERSION,
                    "lease_id": lease_id,
                    "pid": os.getpid(),
                    "created_at": _now_iso(),
                },
                handle,
                indent=2,
            )
            handle.write("\n")
        yield
    finally:
        try:
            read_flags = os.O_RDONLY
            if hasattr(os, "O_NOFOLLOW"):
                read_flags |= os.O_NOFOLLOW
            read_descriptor = os.open(
                lease_path.name,
                read_flags,
                dir_fd=lease_directory_descriptor,
            )
            with os.fdopen(read_descriptor, "r", encoding="utf-8") as handle:
                current = json.load(handle)
        except (OSError, json.JSONDecodeError):
            current = None
        if isinstance(current, dict) and current.get("lease_id") == lease_id:
            try:
                os.unlink(lease_path.name, dir_fd=lease_directory_descriptor)
            except FileNotFoundError:
                pass
        os.close(lease_directory_descriptor)
        if parent_descriptor is not None:
            os.close(parent_descriptor)


def build_orchestration_prompt(
    *,
    repo_root: Path,
    run_dir: Path,
    config: IdeaLoopConfig,
    seed: str | None,
) -> str:
    seed_line = (
        seed
        if seed
        else "No seed supplied. Discover a fresh opportunity from repo evidence."
    )
    return f"""Use $a-story-instagram-idea-loop to run one bounded Instagram idea loop.

Exact run directory (the only path you may write):
{run_dir}

Repository evidence root (read-only; never edit it):
{repo_root}

Seed:
{seed_line}

Budgets:
- maximum iterations: {config.max_iterations}
- maximum candidates per iteration: {config.candidate_budget}

Read `.internal/loop-state.json` and `.internal/evidence-manifest.json` inside
the run directory first. Load the exact artifact field contract with:
{repo_root}/venv/bin/python {repo_root}/scripts/instagram_idea_loop.py schema

Follow the skill exactly. Use project custom agents
`asot_idea_scout`, `asot_idea_maker`, and `asot_idea_verifier`; the controller
must not impersonate their independent outputs. Spawn two maker tasks with
different creative lanes, two blind verifier tasks with different lenses, and
a fresh selector task. The first line of every spawn prompt must be exactly
`ASOT_IDEA_LOOP_ROLE=<custom-agent-name>`, using one of the three names above.
Store the exact returned receiver thread ID as each artifact's task ID; live
validation matches those IDs exactly against completed Codex spawn events.
Give critics only the author-hidden card produced by the schema contract and
bind their reviews to both the exact candidate and blind input fingerprints.
The controller alone writes artifacts.

Iterate generate -> blind verify -> scoped repair -> fresh verify until one
route satisfies every stop condition or an honest terminal state is reached.
Never lower thresholds, expose below-threshold routes in `creator-brief.md`,
invent creator approval, package a carousel, generate images, publish, edit
durable memory, or claim guaranteed virality. On success stop at
READY_FOR_CONCEPT_LOCK with creator approval PENDING.

Before finishing, run:
{repo_root}/venv/bin/python {repo_root}/scripts/instagram_idea_loop.py validate {run_dir}
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
    evidence = build_evidence_manifest(repo_root, run_id=run_id, now=now)
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
            repo_root=repo_root,
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


def _resume_run_locked(run_dir: Path) -> LoopState:
    state = load_state(run_dir)
    if (
        state.status == SUCCESS_STATUS or state.status in HONEST_STOP_STATUSES
    ) and controller_finalization_valid(run_dir, state):
        raise ValueError(f"terminal run {state.run_id!r} cannot be resumed from {state.status}")
    return update_loop_state(
        run_dir,
        status="RUNNING",
        stage=state.stage,
        stop_reason="",
        event="run_resumed",
    )


def resume_run(run_dir: Path) -> LoopState:
    with execution_lease(run_dir):
        return _resume_run_locked(run_dir)


def _parse_model(path: Path, model: type[BaseModel], errors: list[str]) -> BaseModel | None:
    try:
        return model.model_validate(_load_json(path))
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        errors.append(f"{path.name}: {exc}")
        return None


def _evidence_records(
    manifest: dict[str, Any],
    errors: list[str],
) -> tuple[Path | None, dict[str, dict[str, Any]]]:
    raw_root = manifest.get("repo_root")
    if not isinstance(raw_root, str) or not raw_root.strip():
        errors.append("evidence-manifest.json: repo_root must be an absolute path")
        return None, {}
    repo_root = Path(raw_root).expanduser()
    if not repo_root.is_absolute():
        errors.append("evidence-manifest.json: repo_root must be an absolute path")
        return None, {}
    repo_root = repo_root.resolve()
    if repo_root != PROJECT_ROOT:
        errors.append(
            "evidence-manifest.json: repo_root must equal the controller project root"
        )
        return None, {}
    records: dict[str, dict[str, Any]] = {}
    allowed_dynamic_paths = {
        _relative(repo_root, path)
        for pattern in DYNAMIC_EVIDENCE_GLOBS
        for path in repo_root.glob(pattern)
        if path.is_file()
        and path.resolve().is_relative_to(repo_root)
        and path.suffix.lower() in EVIDENCE_SUFFIXES
        and path.stat().st_size <= MAX_EVIDENCE_FILE_BYTES
    }
    for group in ("core", "dynamic"):
        raw_records = manifest.get(group, [])
        if not isinstance(raw_records, list):
            errors.append(f"evidence-manifest.json: {group} must be a list")
            continue
        for record in raw_records:
            if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                errors.append(f"evidence-manifest.json: malformed {group} record")
                continue
            reference = str(record["path"])
            relative = Path(reference)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(
                    f"evidence-manifest.json: path must be repo-relative: {reference!r}"
                )
                continue
            if group == "dynamic" and reference not in allowed_dynamic_paths:
                errors.append(
                    f"evidence-manifest.json: dynamic path is outside the allowlist: {reference!r}"
                )
                continue
            if group == "dynamic":
                if reference.startswith(("output/concepts/", "output/carousels/")):
                    expected_purpose = "collision_check_only"
                elif reference.startswith(("corpus/posts/", "corpus/reels/")):
                    expected_purpose = "owned_account_signal"
                else:
                    expected_purpose = "external_or_report_signal"
                if record.get("purpose") != expected_purpose:
                    errors.append(
                        "evidence-manifest.json: evidence purpose mismatch for "
                        f"{reference!r}"
                    )
                    continue
            if reference in records:
                errors.append(f"evidence-manifest.json: duplicate path {reference!r}")
                continue
            records[reference] = record
    return repo_root, records


def _validate_evidence_references(
    *,
    label: str,
    references: list[str],
    repo_root: Path | None,
    records: dict[str, dict[str, Any]],
    errors: list[str],
    allow_unavailable: bool = False,
    allowed_purposes: set[str | None] | None = None,
) -> None:
    if repo_root is None:
        return
    for reference in references:
        relative = Path(reference)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{label}: evidence path must be repo-relative: {reference!r}")
            continue
        record = records.get(reference)
        if record is None:
            errors.append(f"{label}: evidence path is absent from manifest: {reference!r}")
            continue
        purpose = record.get("purpose")
        if allowed_purposes is not None and purpose not in allowed_purposes:
            errors.append(
                f"{label}: evidence purpose {purpose!r} is not allowed for "
                f"{reference!r}"
            )
            continue
        if not record.get("exists"):
            if not allow_unavailable:
                errors.append(f"{label}: evidence path was unavailable: {reference!r}")
            continue
        current_path = (repo_root / relative).resolve()
        if not current_path.is_relative_to(repo_root):
            errors.append(f"{label}: evidence path escapes repo root: {reference!r}")
            continue
        if not current_path.is_file():
            errors.append(f"{label}: evidence file no longer exists: {reference!r}")
            continue
        recorded_hash = record.get("sha256")
        if not isinstance(recorded_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded_hash):
            errors.append(f"{label}: manifest hash is missing for {reference!r}")
            continue
        if _sha256_file(current_path) != recorded_hash:
            errors.append(f"{label}: evidence changed after manifest capture: {reference!r}")


def _validate_source_evidence(
    *,
    source: SourceMemoryBrief,
    repo_root: Path | None,
    records: dict[str, dict[str, Any]],
    errors: list[str],
    allow_unavailable: bool = False,
) -> None:
    _validate_evidence_references(
        label="source-memory-brief.json supporting evidence",
        references=source.evidence_paths,
        repo_root=repo_root,
        records=records,
        errors=errors,
        allow_unavailable=allow_unavailable,
        allowed_purposes=SUPPORTING_EVIDENCE_PURPOSES,
    )
    _validate_evidence_references(
        label="source-memory-brief.json collision evidence",
        references=source.collision_paths,
        repo_root=repo_root,
        records=records,
        errors=errors,
        allow_unavailable=allow_unavailable,
        allowed_purposes=COLLISION_EVIDENCE_PURPOSES,
    )


def _validate_candidate_evidence(
    *,
    candidate: IdeaCandidate,
    repo_root: Path | None,
    records: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    label = f"candidate {candidate.candidate_id}"
    _validate_evidence_references(
        label=f"{label} supporting evidence",
        references=candidate.evidence_paths,
        repo_root=repo_root,
        records=records,
        errors=errors,
        allowed_purposes=SUPPORTING_EVIDENCE_PURPOSES,
    )
    _validate_evidence_references(
        label=f"{label} collision evidence",
        references=candidate.collision_paths,
        repo_root=repo_root,
        records=records,
        errors=errors,
        allowed_purposes=COLLISION_EVIDENCE_PURPOSES,
    )
    if candidate.moment_origin != "documented_repo_story":
        return
    origin_path = candidate.moment_origin_path
    if origin_path not in candidate.evidence_paths:
        errors.append(
            f"{label}: documented moment_origin_path must also be supporting evidence"
        )
        return
    origin_record = records.get(origin_path or "")
    if origin_record is None:
        return
    if origin_record.get("purpose") != "owned_account_signal":
        errors.append(
            f"{label}: documented lived-story origin must bind to an "
            "owned_account_signal record"
        )


def _computed_external_freshness(
    repo_root: Path | None,
    records: dict[str, dict[str, Any]],
    *,
    now: datetime | None = None,
) -> tuple[str, int | None]:
    if repo_root is None:
        return "UNKNOWN", None
    newest: datetime | None = None
    for reference, record in records.items():
        if not reference.startswith(
            ("corpus/forensic-instagram/", "corpus/competitors/")
        ):
            continue
        path = repo_root / reference
        if not record.get("exists") or not path.is_file():
            continue
        observed = _source_date(path)
        if observed is None:
            observed = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        newest = max(newest, observed) if newest else observed
    if newest is None:
        return "MISSING", None
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if newest > current + FUTURE_EVIDENCE_TOLERANCE:
        return "FUTURE", (current - newest).days
    age_days = (current - newest).days
    return ("CURRENT" if age_days <= 30 else "STALE"), age_days


def _validate_agent_separation(
    *,
    pool: CandidatePool,
    verification: VerificationBundle,
    errors: list[str],
    label: str,
    require_every_candidate_reviewed: bool,
) -> set[str]:
    maker_tasks = {candidate.maker_task_id for candidate in pool.candidates}
    maker_tasks.update(
        candidate.repair_task_id
        for candidate in pool.candidates
        if candidate.repair_task_id is not None
    )
    initial_maker_tasks = {candidate.maker_task_id for candidate in pool.candidates}
    if len(initial_maker_tasks) < 2:
        errors.append(f"{label}: candidate pool requires two distinct maker task IDs")

    candidates = {candidate.candidate_id: candidate for candidate in pool.candidates}
    review_tasks: set[str] = set()
    reviews_by_candidate: dict[str, set[str]] = {}
    lenses_by_candidate: dict[str, set[str]] = {}
    for review in verification.reviews:
        review_tasks.add(review.verifier_task_id)
        reviews_by_candidate.setdefault(review.candidate_id, set()).add(review.verifier_task_id)
        lenses_by_candidate.setdefault(review.candidate_id, set()).add(review.verifier_lens)
        candidate = candidates.get(review.candidate_id)
        if candidate is None:
            errors.append(f"{label}: review references unknown candidate {review.candidate_id!r}")
            continue
        if review.maker_task_id != candidate.maker_task_id:
            errors.append(f"{label}: review maker provenance mismatch for {review.candidate_id}")
        if review.verifier_task_id in maker_tasks:
            errors.append(
                f"{label}: verifier task {review.verifier_task_id!r} overlaps a maker task"
            )

    if require_every_candidate_reviewed:
        for candidate_id in candidates:
            if len(reviews_by_candidate.get(candidate_id, set())) < 2:
                errors.append(f"{label}: candidate {candidate_id} requires two verifier tasks")
            if lenses_by_candidate.get(candidate_id, set()) != {
                "audience_distribution",
                "stage_scene_taste_safety",
            }:
                errors.append(
                    f"{label}: candidate {candidate_id} requires both verifier lenses"
                )

    selector_task = verification.selector.selector_task_id
    if selector_task in maker_tasks:
        errors.append(f"{label}: selector task overlaps a maker task")
    if selector_task in review_tasks:
        errors.append(f"{label}: selector task overlaps a critic task")
    if not set(verification.selector.critic_task_ids).issubset(review_tasks):
        errors.append(f"{label}: selector cites critic tasks absent from reviews")
    return maker_tasks | review_tasks | {selector_task}


def _validate_review_fingerprints(
    *,
    pool_path: Path,
    pool: CandidatePool,
    verification: VerificationBundle,
    errors: list[str],
    label: str,
) -> None:
    try:
        raw_pool = _load_json(pool_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: {exc}")
        return
    raw_candidates = {
        str(candidate.get("candidate_id")): candidate
        for candidate in raw_pool.get("candidates", [])
        if isinstance(candidate, dict) and candidate.get("candidate_id")
    }
    models = {candidate.candidate_id: candidate for candidate in pool.candidates}
    for review in verification.reviews:
        raw_candidate = raw_candidates.get(review.candidate_id)
        candidate = models.get(review.candidate_id)
        if raw_candidate is None or candidate is None:
            continue
        if review.candidate_sha256 != candidate_fingerprint(raw_candidate):
            errors.append(f"{label}: stale candidate fingerprint for {review.candidate_id}")
        if review.blind_input_sha256 != blind_candidate_fingerprint(raw_candidate):
            errors.append(f"{label}: stale blind fingerprint for {review.candidate_id}")


def _validate_critic_inputs(
    *,
    run_dir: Path,
    state: LoopState,
    pool_path: Path,
    pool: CandidatePool,
    verification: VerificationBundle,
    errors: list[str],
    label: str,
) -> None:
    try:
        raw_pool = _load_json(pool_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: {exc}")
        return
    raw_candidates = {
        str(candidate.get("candidate_id")): candidate
        for candidate in raw_pool.get("candidates", [])
        if isinstance(candidate, dict) and candidate.get("candidate_id")
    }
    models = {candidate.candidate_id: candidate for candidate in pool.candidates}
    for review in verification.reviews:
        critic_input_path = (
            run_dir
            / ".internal"
            / "critic-inputs"
            / review.verifier_task_id
            / f"{review.candidate_id}.json"
        )
        critic_input = _parse_model(critic_input_path, CriticInputRecord, errors)
        if not isinstance(critic_input, CriticInputRecord):
            continue
        raw_candidate = raw_candidates.get(review.candidate_id)
        candidate = models.get(review.candidate_id)
        if raw_candidate is None or candidate is None:
            continue
        expected_card = blind_candidate_card(raw_candidate)
        expected_hash = blind_candidate_fingerprint(raw_candidate)
        if critic_input.run_id != state.run_id:
            errors.append(f"{label}: critic input run_id mismatch")
        if critic_input.iteration != candidate.iteration:
            errors.append(f"{label}: critic input iteration mismatch for {review.candidate_id}")
        if critic_input.verifier_task_id != review.verifier_task_id:
            errors.append(f"{label}: critic input verifier task mismatch")
        if critic_input.verifier_lens != review.verifier_lens:
            errors.append(f"{label}: critic input verifier lens mismatch")
        if critic_input.candidate_id != review.candidate_id:
            errors.append(f"{label}: critic input candidate mismatch")
        if critic_input.blind_input_sha256 != expected_hash:
            errors.append(f"{label}: critic input fingerprint is stale")
        if critic_input.card != expected_card:
            errors.append(f"{label}: critic input card is not the canonical blind projection")


def _iteration_artifacts(
    run_dir: Path,
    state: LoopState,
    errors: list[str],
    *,
    require_every_candidate_reviewed: bool,
) -> list[tuple[int, Path, CandidatePool, VerificationBundle, dict[str, Any]]]:
    if state.iteration < 1:
        errors.append("evaluated terminal state requires at least one iteration")
        return []
    artifacts: list[tuple[int, Path, CandidatePool, VerificationBundle, dict[str, Any]]] = []
    for iteration in range(1, state.iteration + 1):
        iteration_dir = run_dir / ".internal" / "iterations" / f"{iteration:02d}"
        pool_path = iteration_dir / "concept-routes.json"
        verification_path = iteration_dir / "verification.json"
        pool = _parse_model(pool_path, CandidatePool, errors)
        verification = _parse_model(verification_path, VerificationBundle, errors)
        if not isinstance(pool, CandidatePool) or not isinstance(verification, VerificationBundle):
            continue
        if pool.run_id != state.run_id or verification.run_id != state.run_id:
            errors.append(f"iteration {iteration:02d}: run_id must match loop state")
        if len(pool.candidates) > state.candidate_budget:
            errors.append(
                f"iteration {iteration:02d}: candidate budget exceeded "
                f"({len(pool.candidates)} > {state.candidate_budget})"
            )
        for candidate in pool.candidates:
            if candidate.iteration != iteration:
                errors.append(
                    f"iteration {iteration:02d}: candidate {candidate.candidate_id} "
                    f"declares iteration {candidate.iteration}"
                )
        try:
            raw_verification = _load_json(verification_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"iteration {iteration:02d} verification: {exc}")
            continue
        _validate_agent_separation(
            pool=pool,
            verification=verification,
            errors=errors,
            label=f"iteration {iteration:02d}",
            require_every_candidate_reviewed=require_every_candidate_reviewed,
        )
        _validate_review_fingerprints(
            pool_path=pool_path,
            pool=pool,
            verification=verification,
            errors=errors,
            label=f"iteration {iteration:02d}",
        )
        _validate_critic_inputs(
            run_dir=run_dir,
            state=state,
            pool_path=pool_path,
            pool=pool,
            verification=verification,
            errors=errors,
            label=f"iteration {iteration:02d}",
        )
        artifacts.append((iteration, pool_path, pool, verification, raw_verification))

    seen_candidate_ids: set[str] = set()
    for iteration, _, pool, _, _ in artifacts:
        for candidate in pool.candidates:
            if candidate.candidate_id in seen_candidate_ids:
                errors.append(
                    f"iteration {iteration:02d}: candidate ID was reused: "
                    f"{candidate.candidate_id}"
                )
            if (
                iteration > 1
                and candidate.parent_candidate_id not in seen_candidate_ids
            ):
                errors.append(
                    f"iteration {iteration:02d}: candidate {candidate.candidate_id} "
                    "does not reference a candidate from an earlier iteration"
                )
        seen_candidate_ids.update(candidate.candidate_id for candidate in pool.candidates)
    return artifacts


def _validate_cross_iteration_provenance(
    artifacts: list[tuple[int, Path, CandidatePool, VerificationBundle, dict[str, Any]]],
    errors: list[str],
) -> set[str]:
    all_makers: set[str] = set()
    all_critics: set[str] = set()
    all_selectors: set[str] = set()
    seen_critics: set[str] = set()
    for iteration, _, pool, verification, _ in artifacts:
        iteration_makers = {candidate.maker_task_id for candidate in pool.candidates}
        iteration_makers.update(
            candidate.repair_task_id
            for candidate in pool.candidates
            if candidate.repair_task_id is not None
        )
        iteration_critics = {
            review.verifier_task_id for review in verification.reviews
        }
        selector = verification.selector.selector_task_id
        if iteration_critics & seen_critics:
            errors.append(
                f"iteration {iteration:02d}: critic task IDs must be fresh after repair"
            )
        if selector in all_selectors:
            errors.append(
                f"iteration {iteration:02d}: selector task ID must be fresh"
            )
        seen_critics.update(iteration_critics)
        all_makers.update(iteration_makers)
        all_critics.update(iteration_critics)
        all_selectors.add(selector)

    maker_critic_overlap = all_makers & all_critics
    maker_selector_overlap = all_makers & all_selectors
    critic_selector_overlap = all_critics & all_selectors
    if maker_critic_overlap:
        errors.append(
            "cross-iteration task role overlap between maker and critic: "
            f"{sorted(maker_critic_overlap)}"
        )
    if maker_selector_overlap:
        errors.append(
            "cross-iteration task role overlap between maker and selector: "
            f"{sorted(maker_selector_overlap)}"
        )
    if critic_selector_overlap:
        errors.append(
            "cross-iteration task role overlap between critic and selector: "
            f"{sorted(critic_selector_overlap)}"
        )
    return all_makers | all_critics | all_selectors


def _validate_failure_history(
    *,
    state: LoopState,
    artifacts: list[
        tuple[int, Path, CandidatePool, VerificationBundle, dict[str, Any]]
    ],
    successful_final_iteration: bool,
    errors: list[str],
) -> list[str]:
    expected_payloads = artifacts[:-1] if successful_final_iteration else artifacts
    expected = [failure_signature(raw) for *_, raw in expected_payloads]
    recorded = [
        str(event.get("failure_signature"))
        for event in state.history
        if event.get("event") == "verification_failed"
        and event.get("failure_signature")
    ]
    if expected and recorded[-len(expected) :] != expected:
        errors.append(
            "loop-state history must contain the computed failure signature for "
            "every failed iteration"
        )
    if not expected and recorded:
        errors.append("loop-state history records failures for a run with no failed rounds")
    return [failure_signature(raw) for *_, raw in artifacts]


def _first_adjacent_repeat(signatures: list[str]) -> int | None:
    """Return the index of the second item in the first adjacent repeat."""

    for index in range(1, len(signatures)):
        if signatures[index] == signatures[index - 1]:
            return index
    return None


def _validate_live_agent_attestation(
    *,
    run_dir: Path,
    source: SourceMemoryBrief,
    artifacts: list[
        tuple[int, Path, CandidatePool, VerificationBundle, dict[str, Any]]
    ],
    errors: list[str],
) -> None:
    execution_dirs = sorted((run_dir / ".internal" / "executions").glob("run-*"))
    if not execution_dirs:
        errors.append("live run is missing Codex execution provenance")
        return
    attested_roles: dict[str, str] = {}
    completed_tasks: set[str] = set()
    event_logs = 0
    for execution_dir in execution_dirs:
        events_path = execution_dir / "codex-events.jsonl"
        if not events_path.is_file():
            continue
        event_logs += 1
        line_number = 0
        try:
            for line_number, line in enumerate(
                events_path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if not line.strip():
                    continue
                event = json.loads(line)
                if not isinstance(event, dict):
                    continue
                item = event.get("item")
                if not isinstance(item, dict):
                    continue
                if (
                    event.get("type") != "item.completed"
                    or item.get("type") != "collab_tool_call"
                    or item.get("status") != "completed"
                ):
                    continue
                receiver_ids = item.get("receiver_thread_ids")
                agent_states = item.get("agents_states")
                if (
                    not isinstance(receiver_ids, list)
                    or not all(isinstance(value, str) for value in receiver_ids)
                    or not isinstance(agent_states, dict)
                ):
                    errors.append(
                        f"malformed completed collab event at {events_path}:{line_number}"
                    )
                    continue
                for receiver_id, raw_state in agent_states.items():
                    if not isinstance(receiver_id, str) or not isinstance(raw_state, dict):
                        continue
                    if (
                        raw_state.get("status") == "completed"
                        and isinstance(raw_state.get("message"), str)
                        and raw_state["message"].strip()
                    ):
                        completed_tasks.add(receiver_id)
                if item.get("tool") != "spawn_agent":
                    continue
                prompt = item.get("prompt")
                if not isinstance(prompt, str):
                    errors.append(
                        f"completed spawn event lacks a prompt at "
                        f"{events_path}:{line_number}"
                    )
                    continue
                first_line = prompt.splitlines()[0].strip() if prompt.splitlines() else ""
                marker = IDEA_AGENT_ROLE_MARKER.fullmatch(first_line)
                if marker is None:
                    continue
                role = marker.group(1)
                for receiver_id in receiver_ids:
                    state = agent_states.get(receiver_id)
                    state_status = (
                        state.get("status") if isinstance(state, dict) else None
                    )
                    if state_status in {
                        "errored",
                        "interrupted",
                        "not_found",
                        "shutdown",
                    }:
                        errors.append(
                            "completed spawn event has a failed agent state for "
                            f"{receiver_id}: {state_status}"
                        )
                        continue
                    previous = attested_roles.get(receiver_id)
                    if previous is not None and previous != role:
                        errors.append(
                            f"agent thread {receiver_id} is attested to multiple roles"
                        )
                        continue
                    attested_roles[receiver_id] = role
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(
                "Codex event provenance is unreadable at "
                f"{events_path}:{line_number}: {exc}"
            )
    if event_logs == 0:
        errors.append("live run is missing Codex JSONL event provenance")
        return

    required: set[tuple[str, str]] = {
        (source.scout_task_id, "asot_idea_scout"),
    }
    for _, _, pool, verification, _ in artifacts:
        required.update(
            (candidate.maker_task_id, "asot_idea_maker")
            for candidate in pool.candidates
        )
        required.update(
            (candidate.repair_task_id, "asot_idea_maker")
            for candidate in pool.candidates
            if candidate.repair_task_id is not None
        )
        required.update(
            (review.verifier_task_id, "asot_idea_verifier")
            for review in verification.reviews
        )
        required.add(
            (verification.selector.selector_task_id, "asot_idea_verifier")
        )
    for task_id, agent_name in sorted(required):
        if attested_roles.get(task_id) != agent_name:
            errors.append(
                "Codex event log does not attest task/agent provenance: "
                f"{task_id} ({agent_name})"
            )
        if task_id not in completed_tasks:
            errors.append(
                "Codex event log does not attest a completed agent result: "
                f"{task_id} ({agent_name})"
            )


def validate_run(
    run_dir: Path,
    *,
    require_live_attestation: bool = False,
) -> ValidationReport:
    run_dir = run_dir.expanduser().absolute()
    unsafe_entry = _unsafe_run_entry(run_dir)
    if unsafe_entry:
        return ValidationReport(
            run_dir=str(run_dir),
            status="INVALID_OUTPUT",
            valid=False,
            errors=(unsafe_entry,),
        )
    run_dir = run_dir.resolve()
    errors: list[str] = []
    if require_live_attestation:
        warnings: list[str] = [
            (
                "Live validation exactly matches completed spawn receiver IDs and "
                "role markers. Codex JSONL does not expose the selected custom-agent "
                "config, so the role selection itself remains instruction-enforced."
            )
        ]
    else:
        warnings = [
            (
                "Offline validation checks distinct task IDs and fingerprints but "
                "does not inspect Codex execution provenance and does not "
                "cryptographically attest agent execution."
            )
        ]
    external_evidence_status = "UNKNOWN"
    blocking_evidence_issue = False
    manifest_repo_root: Path | None = None
    evidence_records: dict[str, dict[str, Any]] = {}
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
            if not isinstance(evidence, dict):
                raise AttributeError("manifest must contain an object")
            manifest_repo_root, evidence_records = _evidence_records(evidence, errors)
            if evidence.get("run_id") != state.run_id:
                errors.append("evidence-manifest.json: run_id must match loop state")
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
                message = f"required evidence files are unavailable: {unavailable_core}"
                blocking_evidence_issue = True
                if state.status == "STALE_EVIDENCE":
                    warnings.append(message)
                else:
                    errors.append(message)
            if evidence.get("freshness", {}).get("external_snapshot_status") != "CURRENT":
                warnings.append(
                    "external Instagram/competitor evidence is missing, stale, "
                    "or future-dated"
                )
            external_evidence_status, external_age_days = _computed_external_freshness(
                manifest_repo_root,
                evidence_records,
            )
            if external_evidence_status != "CURRENT":
                blocking_evidence_issue = True
            declared_freshness = evidence.get("freshness", {})
            if declared_freshness.get("external_snapshot_status") != external_evidence_status:
                errors.append(
                    "evidence-manifest.json: external freshness status does not "
                    "match current source dates"
                )
            if (
                declared_freshness.get("newest_external_snapshot_age_days")
                != external_age_days
            ):
                errors.append(
                    "evidence-manifest.json: external freshness age does not "
                    "match current source dates"
                )
            _validate_evidence_references(
                label="core evidence",
                references=list(CORE_EVIDENCE_PATHS),
                repo_root=manifest_repo_root,
                records=evidence_records,
                errors=errors,
                allow_unavailable=state.status == "STALE_EVIDENCE",
            )
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            errors.append(f"evidence-manifest.json: {exc}")

    if state.status in HONEST_STOP_STATUSES:
        if not state.stop_reason.strip():
            errors.append("honest stop state requires a concrete stop_reason")
        if state.final_candidate_id:
            errors.append("honest stop state must not expose a final candidate")
        for relative in REQUIRED_STOP_BASE_ARTIFACTS:
            if not (run_dir / relative).is_file():
                errors.append(f"honest stop is missing {relative}")
        source_model = None
        if (run_dir / "source-memory-brief.json").is_file():
            source_model = _parse_model(
                run_dir / "source-memory-brief.json", SourceMemoryBrief, errors
            )
        if isinstance(source_model, SourceMemoryBrief):
            if source_model.run_id != state.run_id:
                errors.append("source-memory-brief.json: run_id must match loop state")
            _validate_source_evidence(
                source=source_model,
                repo_root=manifest_repo_root,
                records=evidence_records,
                errors=errors,
                allow_unavailable=state.status == "STALE_EVIDENCE",
            )

        evaluated_stop = state.status in {"NO_GO", "STAGNATED", "BUDGET_EXHAUSTED"}
        if evaluated_stop:
            for relative in REQUIRED_EVALUATED_STOP_ARTIFACTS:
                if not (run_dir / relative).is_file():
                    errors.append(f"evaluated stop is missing {relative}")
            pool_path = run_dir / "concept-routes.json"
            verification_path = run_dir / "verification.json"
            pool_model = _parse_model(pool_path, CandidatePool, errors)
            verification_model = _parse_model(
                verification_path, VerificationBundle, errors
            )
            loop_tasks: set[str] = set()
            if isinstance(pool_model, CandidatePool) and isinstance(
                verification_model, VerificationBundle
            ):
                if (
                    pool_model.run_id != state.run_id
                    or verification_model.run_id != state.run_id
                ):
                    errors.append("evaluated stop artifacts must match loop-state run_id")
                if verification_model.selector.verdict != "NO_GO":
                    errors.append("evaluated stop requires a NO_GO selector verdict")
                if any(
                    review.satisfies_completion
                    for review in verification_model.reviews
                ):
                    errors.append("evaluated stop cannot discard a fully passing route")
                if state.status == "NO_GO":
                    reviews_by_candidate: dict[str, list[VerificationRecord]] = {}
                    for review in verification_model.reviews:
                        reviews_by_candidate.setdefault(review.candidate_id, []).append(
                            review
                        )
                    for candidate in pool_model.candidates:
                        reviews = reviews_by_candidate.get(candidate.candidate_id, [])
                        has_nonrepairable_stop = any(
                            review.verdict == "STOP"
                            or review.stage_scene_gate == "STOP"
                            or review.taste_gate == "STOP"
                            or review.safety_gate == "STOP"
                            or bool(review.exclusion_hits)
                            or bool(review.hard_failures)
                            for review in reviews
                        )
                        if not has_nonrepairable_stop:
                            errors.append(
                                "NO_GO requires a documented non-repairable stop for "
                                f"candidate {candidate.candidate_id}"
                            )
                loop_tasks = _validate_agent_separation(
                    pool=pool_model,
                    verification=verification_model,
                    errors=errors,
                    label="evaluated stop",
                    require_every_candidate_reviewed=True,
                )
                _validate_review_fingerprints(
                    pool_path=pool_path,
                    pool=pool_model,
                    verification=verification_model,
                    errors=errors,
                    label="evaluated stop",
                )
                for candidate in pool_model.candidates:
                    _validate_candidate_evidence(
                        candidate=candidate,
                        repo_root=manifest_repo_root,
                        records=evidence_records,
                        errors=errors,
                    )
                if (
                    isinstance(source_model, SourceMemoryBrief)
                    and source_model.scout_task_id in loop_tasks
                ):
                    errors.append(
                        "scout task must be distinct from maker, critic, and selector tasks"
                    )

            iterations = _iteration_artifacts(
                run_dir,
                state,
                errors,
                require_every_candidate_reviewed=True,
            )
            iteration_tasks = _validate_cross_iteration_provenance(iterations, errors)
            signatures = _validate_failure_history(
                state=state,
                artifacts=iterations,
                successful_final_iteration=False,
                errors=errors,
            )
            if (
                isinstance(source_model, SourceMemoryBrief)
                and source_model.scout_task_id in iteration_tasks
            ):
                errors.append(
                    "scout task must be distinct from all iteration task roles"
                )
            if require_live_attestation and isinstance(source_model, SourceMemoryBrief):
                _validate_live_agent_attestation(
                    run_dir=run_dir,
                    source=source_model,
                    artifacts=iterations,
                    errors=errors,
                )
            if iterations:
                _, last_pool_path, _, _, _ = iterations[-1]
                last_verification_path = last_pool_path.parent / "verification.json"
                if pool_path.is_file() and _sha256_file(pool_path) != _sha256_file(last_pool_path):
                    errors.append("concept-routes.json must match the final iteration snapshot")
                if (
                    verification_path.is_file()
                    and _sha256_file(verification_path) != _sha256_file(last_verification_path)
                ):
                    errors.append("verification.json must match the final iteration snapshot")

            repeat_index = _first_adjacent_repeat(signatures)
            if state.status == "STAGNATED":
                if len(signatures) < 2 or signatures[-1] != signatures[-2]:
                    errors.append(
                        "STAGNATED requires the same normalized failure signature twice "
                        "and matching iteration evidence"
                    )
                elif repeat_index != len(signatures) - 1:
                    errors.append(
                        "STAGNATED must stop at the first adjacent repeated "
                        "failure signature"
                    )
            elif repeat_index is not None:
                errors.append(
                    "the loop continued after an adjacent repeated failure "
                    "signature instead of stopping STAGNATED"
                )
            if state.status == "BUDGET_EXHAUSTED" and not signatures:
                errors.append(
                    "BUDGET_EXHAUSTED requires at least one evaluated failure round"
                )
            elif (
                state.status == "BUDGET_EXHAUSTED"
                and len(signatures) >= 2
                and signatures[-1] == signatures[-2]
            ):
                errors.append(
                    "BUDGET_EXHAUSTED requires changing final failure signatures; "
                    "a repeat must stop as STAGNATED"
                )
        else:
            stop_path = run_dir / "stop-evidence.json"
            if not stop_path.is_file():
                errors.append("early stop is missing stop-evidence.json")
            stop_model = (
                _parse_model(stop_path, StopEvidence, errors)
                if stop_path.is_file()
                else None
            )
            if isinstance(stop_model, StopEvidence):
                if stop_model.run_id != state.run_id:
                    errors.append("stop-evidence.json: run_id must match loop state")
                if stop_model.status != state.status:
                    errors.append("stop-evidence.json: status must match loop state")
                if stop_model.reason.strip() != state.stop_reason.strip():
                    errors.append("stop-evidence.json: reason must match loop state")
                _validate_evidence_references(
                    label="stop-evidence.json",
                    references=stop_model.evidence_paths,
                    repo_root=manifest_repo_root,
                    records=evidence_records,
                    errors=errors,
                    allow_unavailable=True,
                    allowed_purposes=SUPPORTING_EVIDENCE_PURPOSES,
                )
            if state.iteration != 0:
                errors.append("early STALE_EVIDENCE/HUMAN_REQUIRED stop requires iteration 0")

        if state.status == "BUDGET_EXHAUSTED" and state.iteration != state.max_iterations:
            errors.append("BUDGET_EXHAUSTED requires iteration == max_iterations")
        if state.status == "STALE_EVIDENCE" and not blocking_evidence_issue:
            errors.append(
                "STALE_EVIDENCE requires at least one missing, stale, or "
                "future-dated required evidence source"
            )
        creator_brief_path = run_dir / "creator-brief.md"
        if creator_brief_path.is_file():
            creator_brief = creator_brief_path.read_text(encoding="utf-8")
            if (
                "will go viral" in creator_brief.lower()
                or "guaranteed to go viral" in creator_brief.lower()
            ):
                errors.append("creator-brief.md must not promise virality")
            if evaluated_stop and isinstance(pool_model, CandidatePool):
                for candidate in pool_model.candidates:
                    if candidate.candidate_id in creator_brief:
                        errors.append("honest-stop creator brief must not promote candidate IDs")
        return ValidationReport(
            run_dir=str(run_dir),
            status=state.status if not errors else "INVALID_OUTPUT",
            valid=not errors,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    if state.status != SUCCESS_STATUS:
        errors.append(
            "loop-state.json: status must be "
            f"{SUCCESS_STATUS} or an honest stop, got {state.status!r}"
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
    source_model = _parse_model(run_dir / "source-memory-brief.json", SourceMemoryBrief, errors)
    debate_model = _parse_model(run_dir / "concept-debate.json", ConceptDebate, errors)
    repairs_model = _parse_model(run_dir / "concept-repairs.json", ConceptRepairs, errors)
    taste_model = _parse_model(run_dir / "taste-gate.json", TasteGateBundle, errors)
    verification_path = run_dir / "verification.json"
    verification_model = _parse_model(verification_path, VerificationBundle, errors)
    selection_path = run_dir / "concept-selection.json"
    selection_model = _parse_model(selection_path, ConceptSelection, errors)
    if not all(
        (
            isinstance(pool_model, CandidatePool),
            isinstance(source_model, SourceMemoryBrief),
            isinstance(debate_model, ConceptDebate),
            isinstance(repairs_model, ConceptRepairs),
            isinstance(taste_model, TasteGateBundle),
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
    source = source_model
    debate = debate_model
    repairs = repairs_model
    taste = taste_model
    verification = verification_model
    selection = selection_model
    per_iteration_counts: dict[int, int] = {}
    for candidate in pool.candidates:
        per_iteration_counts[candidate.iteration] = (
            per_iteration_counts.get(candidate.iteration, 0) + 1
        )
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
        ("source-memory-brief.json", source.run_id),
        ("concept-debate.json", debate.run_id),
        ("concept-repairs.json", repairs.run_id),
        ("taste-gate.json", taste.run_id),
        ("verification.json", verification.run_id),
        ("concept-selection.json", selection.run_id),
    ):
        if artifact_run_id != state.run_id:
            errors.append(f"{artifact_name}: run_id must match loop state")

    loop_tasks = _validate_agent_separation(
        pool=pool,
        verification=verification,
        errors=errors,
        label="successful run",
        require_every_candidate_reviewed=True,
    )
    if source.scout_task_id in loop_tasks:
        errors.append("scout task must be distinct from maker, critic, and selector tasks")
    _validate_source_evidence(
        source=source,
        repo_root=manifest_repo_root,
        records=evidence_records,
        errors=errors,
    )
    for candidate in pool.candidates:
        if candidate.moment_origin == "creator_seed":
            if not state.seed:
                errors.append(
                    f"candidate {candidate.candidate_id}: creator_seed origin "
                    "requires a run seed"
                )
            elif state.seed not in candidate.moment_origin_detail:
                errors.append(
                    f"candidate {candidate.candidate_id}: moment_origin_detail "
                    "must preserve the exact creator seed"
                )
        _validate_candidate_evidence(
            candidate=candidate,
            repo_root=manifest_repo_root,
            records=evidence_records,
            errors=errors,
        )
    iterations = _iteration_artifacts(
        run_dir,
        state,
        errors,
        require_every_candidate_reviewed=True,
    )
    iteration_tasks = _validate_cross_iteration_provenance(iterations, errors)
    success_signatures = _validate_failure_history(
        state=state,
        artifacts=iterations,
        successful_final_iteration=True,
        errors=errors,
    )
    failed_signatures = success_signatures[:-1] if success_signatures else []
    if _first_adjacent_repeat(failed_signatures) is not None:
        errors.append(
            "the loop continued after an adjacent repeated failure signature "
            "instead of stopping STAGNATED"
        )
    if source.scout_task_id in iteration_tasks:
        errors.append("scout task must be distinct from all iteration task roles")
    if require_live_attestation:
        _validate_live_agent_attestation(
            run_dir=run_dir,
            source=source,
            artifacts=iterations,
            errors=errors,
        )
    if iterations:
        _, last_pool_path, _, _, _ = iterations[-1]
        last_verification_path = last_pool_path.parent / "verification.json"
        if _sha256_file(pool_path) != _sha256_file(last_pool_path):
            errors.append("concept-routes.json must match the final iteration snapshot")
        if _sha256_file(verification_path) != _sha256_file(last_verification_path):
            errors.append("verification.json must match the final iteration snapshot")

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
    if taste.selected_candidate_id != selected_id:
        errors.append("taste-gate.json: selected candidate must match loop state")

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
        verifier_lenses = {review.verifier_lens for review in selected_reviews}
        if len(selected_reviews) < 2 or len(verifier_tasks) < 2:
            errors.append("selected candidate requires two distinct blind verifier passes")
        if verifier_lenses != {
            "audience_distribution",
            "stage_scene_taste_safety",
        }:
            errors.append("selected candidate requires both verifier lenses")
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
        debate_record = next(
            (record for record in debate.blind_reviews if record.candidate_id == selected_id),
            None,
        )
        if debate_record is None:
            errors.append("concept-debate.json omits the selected candidate")
        else:
            if debate_record.blind_input_sha256 != expected_blind_hash:
                errors.append("concept-debate.json has a stale blind input fingerprint")
            if set(debate_record.critic_task_ids) != verifier_tasks:
                errors.append("concept-debate.json critic tasks do not match verification")
        taste_record = next(
            (record for record in taste.records if record.candidate_id == selected_id),
            None,
        )
        if taste_record is None:
            errors.append("taste-gate.json omits the selected candidate")
        else:
            if taste_record.verdict != "PASS_NO_CAP":
                errors.append("taste-gate.json selected candidate is capped or failed")
            if set(taste_record.verifier_task_ids) != verifier_tasks:
                errors.append("taste-gate.json verifier tasks do not match verification")
        if selected_model.iteration > 1:
            repair_record = next(
                (record for record in repairs.repairs if record.candidate_id == selected_id),
                None,
            )
            if repair_record is None:
                errors.append("concept-repairs.json omits selected repaired candidate lineage")
            elif (
                repair_record.parent_candidate_id != selected_model.parent_candidate_id
                or repair_record.repair_task_id != selected_model.repair_task_id
            ):
                errors.append("concept-repairs.json lineage does not match selected candidate")

    creator_brief = (run_dir / "creator-brief.md").read_text(encoding="utf-8")
    for heading in REQUIRED_CREATOR_BRIEF_HEADINGS:
        if heading not in creator_brief:
            errors.append(f"creator-brief.md is missing required heading: {heading}")
    if selected_id and selected_id not in creator_brief:
        errors.append("creator-brief.md must name the selected candidate ID")
    for candidate in pool.candidates:
        if candidate.candidate_id == selected_id:
            continue
        leaked_values = (
            candidate.candidate_id,
            candidate.title,
            candidate.alive_premise,
            candidate.concrete_moment,
        )
        if any(value in creator_brief for value in leaked_values):
            errors.append("creator-brief.md exposes a non-selected route")
    if selected_model is not None:
        if (
            selected_model.lived_fact_status == "CREATOR_CONFIRMATION_REQUIRED"
            and (
                "confirm" not in creator_brief.lower()
                or "confirm" not in selection.next_action.lower()
            )
        ):
            errors.append(
                "creator brief and next action must request factual confirmation"
            )
        if (
            selected_model.moment_origin == "generic_relationship_hypothesis"
            and "not a claimed lived fact" not in creator_brief.lower()
        ):
            errors.append(
                "creator-brief.md must label a generic hypothesis as not a claimed lived fact"
            )
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
    working_dir: Path,
    live_search: bool,
) -> list[str]:
    if live_search:
        raise ValueError(
            "live_search is disabled until durable web-source provenance exists"
        )
    command = [codex_path]
    command.extend(
        [
            "-a",
            "never",
            "-c",
            'web_search="disabled"',
            "-c",
            "allow_login_shell=false",
            "-c",
            'shell_environment_policy.inherit="none"',
            "-c",
            "shell_environment_policy.experimental_use_profile=false",
            "-c",
            'shell_environment_policy.set.PATH="/usr/bin:/bin:/usr/sbin:/sbin"',
            "--disable",
            "hooks",
            "-C",
            str(working_dir),
            "exec",
            "--ignore-user-config",
            "--ignore-rules",
            "--ephemeral",
            "--json",
            "-",
        ]
    )
    return command


RunCommand = Callable[..., subprocess.CompletedProcess[str]]


def _terminate_process_group(process_group_id: int) -> None:
    """Best-effort cleanup for all descendants of the isolated Codex process."""

    for termination_signal in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process_group_id, termination_signal)
        except ProcessLookupError:
            return
        except PermissionError:
            return


def _read_bounded_process_output(
    handle: Any,
    *,
    limit: int,
    label: str,
) -> str:
    handle.flush()
    size = os.fstat(handle.fileno()).st_size
    if size > limit:
        raise OSError(f"{label} exceeded the {limit}-byte controller limit")
    handle.seek(0)
    return handle.read().decode("utf-8", errors="replace")


def run_codex_command(
    command: list[str],
    *,
    cwd: Path,
    input: str,
    capture_output: bool,
    text: bool,
    timeout: int,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    """Run Codex in an isolated process group with bounded in-memory output."""

    if not capture_output or not text or check:
        raise ValueError("run_codex_command requires captured text output and check=False")
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            start_new_session=True,
        )
        try:
            process.communicate(input=input, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _terminate_process_group(process.pid)
            process.wait()
            stdout = _read_bounded_process_output(
                stdout_file,
                limit=MAX_CODEX_EVENT_BYTES,
                label="Codex event output",
            )
            stderr = _read_bounded_process_output(
                stderr_file,
                limit=MAX_CODEX_STDERR_BYTES,
                label="Codex stderr",
            )
            raise subprocess.TimeoutExpired(
                command,
                timeout,
                output=stdout,
                stderr=stderr,
            ) from exc
        except BaseException:
            _terminate_process_group(process.pid)
            process.wait()
            raise
        _terminate_process_group(process.pid)
        stdout = _read_bounded_process_output(
            stdout_file,
            limit=MAX_CODEX_EVENT_BYTES,
            label="Codex event output",
        )
        stderr = _read_bounded_process_output(
            stderr_file,
            limit=MAX_CODEX_STDERR_BYTES,
            label="Codex stderr",
        )
        return subprocess.CompletedProcess(
            command,
            process.returncode,
            stdout,
            stderr,
        )


def execute_loop(
    repo_root: Path,
    run_dir: Path,
    *,
    config: IdeaLoopConfig,
    run_command: RunCommand = run_codex_command,
    resume: bool = False,
) -> tuple[int, ValidationReport]:
    repo_root = repo_root.resolve()
    run_dir = run_dir.resolve()
    location_error = execution_location_error(repo_root, run_dir)
    if location_error:
        report = ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=(location_error,),
        )
        return 2, report
    try:
        with execution_lease(run_dir):
            if resume:
                _resume_run_locked(run_dir)
            return _execute_loop_locked(
                repo_root,
                run_dir,
                config=config,
                run_command=run_command,
            )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return 2, ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=(str(exc),),
        )


def _execute_loop_locked(
    repo_root: Path,
    run_dir: Path,
    *,
    config: IdeaLoopConfig,
    run_command: RunCommand,
) -> tuple[int, ValidationReport]:
    internal = run_dir / ".internal"
    unsafe_entry = _unsafe_run_entry(run_dir)
    if unsafe_entry:
        return 2, ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=(unsafe_entry,),
        )
    prompt = (internal / "orchestration-prompt.md").read_text(encoding="utf-8")
    executions_root = internal / "executions"
    execution_number = len(list(executions_root.glob("run-*"))) + 1
    execution_dir = executions_root / f"run-{execution_number:02d}"
    execution_dir.mkdir(parents=True, exist_ok=False)
    expectations = _capture_execution_expectations(
        repo_root,
        run_dir,
        config=config,
    )
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
        return 2, report

    command = build_codex_command(
        codex_path=codex,
        working_dir=run_dir,
        live_search=config.live_search,
    )
    try:
        completed = run_command(
            command,
            cwd=run_dir,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=config.command_timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        unsafe_entry = _unsafe_run_entry(run_dir)
        if unsafe_entry:
            return 2, ValidationReport(
                run_dir=str(run_dir),
                status="EXECUTION_FAILED",
                valid=False,
                errors=(unsafe_entry, str(exc)),
            )
        captured_stdout = getattr(exc, "output", "") or ""
        captured_stderr = getattr(exc, "stderr", "") or ""
        if isinstance(captured_stdout, bytes):
            captured_stdout = captured_stdout.decode("utf-8", errors="replace")
        if isinstance(captured_stderr, bytes):
            captured_stderr = captured_stderr.decode("utf-8", errors="replace")
        _atomic_write_text(
            execution_dir / "codex-events.jsonl",
            str(captured_stdout),
        )
        _atomic_write_text(
            execution_dir / "codex-stderr.log",
            str(captured_stderr),
        )
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
        return 2, report

    unsafe_entry = _unsafe_run_entry(run_dir)
    if unsafe_entry:
        return 2, ValidationReport(
            run_dir=str(run_dir),
            status="EXECUTION_FAILED",
            valid=False,
            errors=(unsafe_entry,),
        )
    _atomic_write_text(execution_dir / "codex-events.jsonl", completed.stdout)
    _atomic_write_text(execution_dir / "codex-stderr.log", completed.stderr)
    integrity_errors = _execution_integrity_errors(run_dir, expectations)
    if integrity_errors:
        report = ValidationReport(
            run_dir=str(run_dir),
            status="INVALID_OUTPUT",
            valid=False,
            errors=tuple(integrity_errors),
        )
        _write_json(internal / "validation.json", report.to_dict())
        _mark_integrity_failure(run_dir, expectations, report.errors)
        return 2, report
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
        return 2, report

    report = validate_run(run_dir, require_live_attestation=True)
    _write_json(internal / "validation.json", report.to_dict())
    if report.valid and report.status == SUCCESS_STATUS:
        _write_controller_finalization(run_dir, report)
        return 0, report
    if report.valid and report.status in HONEST_STOP_STATUSES:
        _write_controller_finalization(run_dir, report)
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
