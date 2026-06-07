"""Pure Telegram keyboard helpers.

The legacy bot still owns routing and state. This module only builds small
``InlineKeyboardMarkup``-compatible dictionaries and helps tests verify that
callback_data values were not lost during UI cleanup.
"""
from __future__ import annotations

from typing import Any, Iterable


Button = dict[str, str]
Keyboard = dict[str, list[list[Button]]]


def button(text: object, callback_data: object) -> Button:
    """Build one inline button while keeping text/callback values as strings."""
    return {"text": str(text), "callback_data": str(callback_data)}


def row(*buttons: Button | None) -> list[Button]:
    """Build a keyboard row and ignore optional ``None`` buttons."""
    return [btn for btn in buttons if btn is not None]


def keyboard(*rows: Iterable[Button] | None) -> Keyboard:
    """Build a Telegram inline_keyboard dict from row iterables."""
    clean_rows: list[list[Button]] = []
    for item in rows:
        if item is None:
            continue
        clean = [btn for btn in item if btn is not None]
        if clean:
            clean_rows.append(clean)
    return {"inline_keyboard": clean_rows}


def callback_values(markup: dict[str, Any] | None) -> list[str]:
    """Return callback_data values in display order for regression tests."""
    values: list[str] = []
    for item in (markup or {}).get("inline_keyboard") or []:
        for btn in item or []:
            if "callback_data" in btn:
                values.append(str(btn["callback_data"]))
    return values


def has_callback(markup: dict[str, Any] | None, callback_data: object) -> bool:
    """Check whether a keyboard contains a specific callback."""
    return str(callback_data) in callback_values(markup)
