"""Pure formatting helpers for signal Win Rate reports.

These helpers do not read or update the Win Rate journal. They only format
already-calculated values for Telegram cards.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def winrate_text(value: Any, unknown: str = "н/д") -> str:
    """Format a Win Rate percentage or return an unknown marker."""
    if value is None:
        return unknown
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return unknown


def signed_percent_text(value: Any, unknown: str = "н/д") -> str:
    """Format a signed percent value such as average edge."""
    if value is None:
        return unknown
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return unknown


def signal_status_icon(status: Any) -> str:
    """Return one compact icon for a Win Rate row status."""
    text = str(status or "").upper()
    return {
        "WIN": "🟢",
        "LOSS": "🔴",
        "FLAT": "⚪",
        "PENDING": "⏳",
    }.get(text, "⚪")


def result_suffix(status: Any, edge: Any = None, due_at: datetime | None = None) -> str:
    """Build the short suffix after a Win Rate row status."""
    text = str(status or "").upper()
    if text == "PENDING" and due_at is not None:
        return f" проверка {due_at.strftime('%H:%M UTC')}"
    if edge is None:
        return ""
    try:
        return f" {float(edge):+.2f}%"
    except (TypeError, ValueError):
        return ""
