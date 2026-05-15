"""Paper trader adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def paper_trader_cycle(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("paper_trader_cycle", *args, **kwargs)


def paper_select_trade_candidate(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("paper_select_trade_candidate", *args, **kwargs)


def paper_trader_scan_tickers(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("paper_trader_scan_tickers", *args, **kwargs)


def format_paper_report(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_paper_report", *args, **kwargs)
