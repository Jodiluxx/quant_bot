"""Risk and entry plan adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def build_trade_risk_decision(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_trade_risk_decision", *args, **kwargs)


def build_entry_plan(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("build_entry_plan", *args, **kwargs)


def format_trade_risk_decision(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_trade_risk_decision", *args, **kwargs)


def format_entry_plan_analysis(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_entry_plan_analysis", *args, **kwargs)


def format_portfolio_risk(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_portfolio_risk", *args, **kwargs)
