"""
Unified response helpers for all API endpoints.

Standard structure: {"code": 0, "message": "ok", "data": {...}}
"""

from typing import Any


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
