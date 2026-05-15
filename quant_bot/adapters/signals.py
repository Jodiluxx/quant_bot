"""Signal engine adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def full_analyze(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("full_analyze", *args, **kwargs)


def format_msg(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_msg", *args, **kwargs)


def format_signal_summary(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_signal_summary", *args, **kwargs)


def format_signal_analysis_details(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_signal_analysis_details", *args, **kwargs)


def format_auto_digest(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_auto_digest", *args, **kwargs)
