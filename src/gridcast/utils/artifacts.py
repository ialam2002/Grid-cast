from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def resolve_commit_hash() -> str:
    env_hash = os.getenv("GRIDCAST_COMMIT_HASH")
    if env_hash:
        return env_hash

    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return "unknown"


def build_model_version(horizon_hours: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"h{horizon_hours}-{now}-{uuid4().hex[:8]}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

