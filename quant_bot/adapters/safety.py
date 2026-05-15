"""Safety and kill-switch adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def build_safety_decision(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_safety_decision", *args, **kwargs)


def format_safety_status(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_safety_status", *args, **kwargs)


def set_safety_observe_only(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("set_safety_observe_only", *args, **kwargs)


def set_safety_pause(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("set_safety_pause", *args, **kwargs)
