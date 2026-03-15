from __future__ import annotations

import json
import math
from typing import Any


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            if isinstance(value, float) and math.isnan(value):
                return None
            return float(value)
        text = str(value).replace(",", ".").strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def safe_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
