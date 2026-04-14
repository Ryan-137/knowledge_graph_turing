from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """统一生成 UTC 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def write_json(file_path: Path, payload: Any) -> None:
    """统一 JSON 输出格式，避免不同流程各写一套。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
