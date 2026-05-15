"""Analytics and performance report adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def paper_data_quality_summary(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("paper_data_quality_summary", *args, **kwargs)


def format_bot_quality_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_bot_quality_report", *args, **kwargs)


def format_setup_analytics_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_setup_analytics_report", *args, **kwargs)
