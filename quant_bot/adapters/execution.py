"""Execution gateway adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def execution_mode(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("execution_mode", *args, **kwargs)


def build_execution_order_plan(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_execution_order_plan", *args, **kwargs)


def format_execution_status(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_execution_status", *args, **kwargs)
