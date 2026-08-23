from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


@dataclass
class JobInput:
    device_id: str
    delivery_contact: str
    creator_name: str
    partner_name: str
    relationship: str          # 'together' | 'sending'
    setting_choice: str        # 'keep' | 'fresh'
    quote_mode: str            # 'own' | 'agent' | 'none'
    quote_copy: str | None
    photo_paths: list[str]
    audio_path: str


@dataclass
class SlidePrompt:
    index: int
    image_prompt: str
    on_image_text: str | None
    use_setting_ref: bool


@dataclass
class Slide:
    index: int
    image_path: str
    caption: str | None


@dataclass
class MatchResult:
    pattern_id: str
    slide_count: int
    beats: list[str]


@dataclass
class Job:
    id: str
    status: JobStatus
    input: JobInput
    story_text: str | None = None
    match: MatchResult | None = None
    slides: list[Slide] = field(default_factory=list)
    error: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    @classmethod
    def new(cls, job_input: JobInput) -> "Job":
        ts = _now()
        return cls(id=uuid.uuid4().hex, status=JobStatus.QUEUED, input=job_input,
                   created_at=ts, updated_at=ts)

    def touch(self) -> None:
        self.updated_at = _now()
