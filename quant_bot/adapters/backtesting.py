"""Backtest and walk-forward optimization adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def run_backtest(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("run_backtest", *args, **kwargs)


def run_walk_forward_optimization(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("run_walk_forward_optimization", *args, **kwargs)
