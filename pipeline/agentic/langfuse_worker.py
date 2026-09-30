"""Isolated, stdin-only Langfuse export worker."""

from __future__ import annotations

import json
import sys
from typing import Any

from pipeline.agentic.langfuse_mirror import _sdk_export


MAX_PAYLOAD_BYTES = 64 * 1024


def _read_payload() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_PAYLOAD_BYTES + 1)
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("Langfuse worker payload is too large")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Langfuse worker payload must be an object")
    return payload


def main() -> int:
    try:
        _sdk_export(_read_payload())
    except Exception as exc:
        print(json.dumps({"status": "failed_nonblocking", "reason": type(exc).__name__}))
        return 1
    print(json.dumps({"status": "mirrored"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
