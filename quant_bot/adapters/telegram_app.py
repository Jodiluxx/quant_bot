"""Telegram UI and scheduler adapter."""
from __future__ import annotations

from typing import Any

from ..legacy import call_legacy


def main_keyboard(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("main_keyboard", *args, **kwargs)


def signal_menu_keyboard(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("signal_menu_keyboard", *args, **kwargs)


def autobot_keyboard(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("autobot_keyboard", *args, **kwargs)


def format_autobot_menu(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("format_autobot_menu", *args, **kwargs)


def auto_settings_keyboard(*args: Any, **kwargs: Any) -> Any:
    return call_legacy("auto_settings_keyboard", *args, **kwargs)


async def async_handle_update(*args: Any, **kwargs: Any) -> Any:
    return await call_legacy("async_handle_update", *args, **kwargs)


async def async_auto_signal_loop(*args: Any, **kwargs: Any) -> Any:
    return await call_legacy("async_auto_signal_loop", *args, **kwargs)
