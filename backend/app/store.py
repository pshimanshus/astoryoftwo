from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from app.models import Job, JobInput, JobStatus, MatchResult, Slide


class JobStore:
    def __init__(self, db_path: Path, blob_root: Path):
        self.db_path = Path(db_path)
        self.blob_root = Path(blob_root)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.blob_root.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT NOT NULL)")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:        # commit on success, rollback on exception
                yield conn
        finally:
            conn.close()      # avoid ResourceWarning on GC

    def create(self, job: Job) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO jobs (id, data) VALUES (?, ?)", (job.id, _dumps(job)))

    def save(self, job: Job) -> None:
        with self._conn() as c:
            c.execute("INSERT INTO jobs (id, data) VALUES (?, ?) "
                      "ON CONFLICT(id) DO UPDATE SET data=excluded.data", (job.id, _dumps(job)))

    def get(self, job_id: str) -> Job | None:
        with self._conn() as c:
            row = c.execute("SELECT data FROM jobs WHERE id=?", (job_id,)).fetchone()
        return _loads(row[0]) if row else None

    def save_blob(self, job_id: str, name: str, data: bytes) -> str:
        d = self.blob_root / job_id
        d.mkdir(parents=True, exist_ok=True)
        path = d / name
        path.write_bytes(data)
        return str(path)

    def read_blob(self, path: str) -> bytes:
        return Path(path).read_bytes()


def _dumps(job: Job) -> str:
    return json.dumps(asdict(job), default=lambda o: o.value if isinstance(o, JobStatus) else o)


def _loads(data: str) -> Job:
    d = json.loads(data)
    d["status"] = JobStatus(d["status"])
    d["input"] = JobInput(**d["input"])
    d["match"] = MatchResult(**d["match"]) if d.get("match") else None
    d["slides"] = [Slide(**s) for s in d.get("slides", [])]
    return Job(**d)
