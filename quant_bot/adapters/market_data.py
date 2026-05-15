"""Market data and futures context adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy, get_bot_module


def get_ohlcv(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("get_ohlcv", *args, **kwargs)


def get_ohlcv_with_times(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("get_ohlcv_with_times", *args, **kwargs)


def get_price(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("get_price", *args, **kwargs)


def futures_api_symbol(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("futures_api_symbol", *args, **kwargs)


def get_futures_context(*args: Any, **kwargs: Any) -> Any:
    bot = get_bot_module()
    builder = getattr(bot, "build_futures_context", None) or getattr(bot, "get_futures_context", None)
    if not callable(builder):
        raise AttributeError("Legacy runtime futures context builder is missing")
    return builder(*args, **kwargs)


def format_futures_context(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_futures_context", *args, **kwargs)
