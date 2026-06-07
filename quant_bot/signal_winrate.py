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


def outcome_hint(status: Any) -> str:
    """Return a short human explanation for a Win Rate outcome."""
    text = str(status or "").upper()
    return {
        "WIN": "в сторону сигнала",
        "LOSS": "против сигнала",
        "FLAT": "нейтрально: слабое движение",
        "PENDING": "ждём закрытия TF",
    }.get(text, "статус не распознан")


def outcome_legend_lines() -> list[str]:
    """Return compact legend lines for Telegram Win Rate cards."""
    return [
        "WIN — цена пошла в сторону сигнала после его TF",
        "LOSS — цена пошла против сигнала",
        "FLAT — движение слабое; это не победа и не поражение",
        "PENDING — сигнал ещё ждёт проверки после своего TF",
    ]


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
