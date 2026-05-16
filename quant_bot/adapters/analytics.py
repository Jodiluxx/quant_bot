"""Analytics and performance report adapter."""
from __future__ import annotations

from typing import Any

from ..analytics_reports import (
    calibration_group,
    calibration_stats,
    probability_bucket,
    probability_value,
)
from ..legacy import call_legacy


def paper_data_quality_summary(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("paper_data_quality_summary", *args, **kwargs)


def format_bot_quality_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_bot_quality_report", *args, **kwargs)


def format_setup_analytics_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_setup_analytics_report", *args, **kwargs)


def format_probability_calibration_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_probability_calibration_report", *args, **kwargs)


def tf_quality_summary(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("tf_quality_summary_v713", *args, **kwargs)


def market_opportunity_scan(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("market_opportunity_scan", *args, **kwargs)


def format_market_opportunities(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_market_opportunities", *args, **kwargs)


def format_period_performance_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_period_performance_report", *args, **kwargs)
