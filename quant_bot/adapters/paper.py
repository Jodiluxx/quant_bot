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


def paper_positions(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_positions", *args, **kwargs)


def paper_closed_trades(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_closed_trades", *args, **kwargs)


def paper_today_open_count(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_today_open_count", *args, **kwargs)


def paper_manage_open_positions(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_manage_open_positions", *args, **kwargs)


def paper_fill_price(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_fill_price_v714", *args, **kwargs)


def paper_take_partial_tp1(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_take_partial_tp1_v714", *args, **kwargs)


def paper_close_position(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_paper_close_position", *args, **kwargs)


def paper_data_quality_summary(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("paper_data_quality_summary", *args, **kwargs)


def paper_strategy_lines(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_strategy_lines_v77", *args, **kwargs)


def paper_directional_factors(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("_directional_factors_v77", *args, **kwargs)
