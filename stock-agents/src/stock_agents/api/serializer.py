from __future__ import annotations

import dataclasses
import math
from datetime import date, datetime
from enum import Enum
from typing import Any


def to_json(obj: Any) -> Any:
    """Rekurencyjnie konwertuje dataclassy, daty, enumy → typy JSON-serializowalne."""
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (int, bool, str)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclasses.fields(obj):
            result[f.name] = to_json(getattr(obj, f.name))
        # dołącz @property zdefiniowane w klasie
        for name in dir(type(obj)):
            if isinstance(getattr(type(obj), name, None), property):
                try:
                    result[name] = to_json(getattr(obj, name))
                except Exception:
                    pass
        return result
    if isinstance(obj, dict):
        return {k: to_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json(item) for item in obj]
    return str(obj)
