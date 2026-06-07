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


def sample_quality_text(counted: Any, min_samples: int = 30) -> str:
    """Explain whether a Win Rate sample is large enough to trust."""
    try:
        count = max(0, int(counted))
    except (TypeError, ValueError):
        count = 0
    minimum = max(1, int(min_samples or 30))
    missing = max(0, minimum - count)
    if count == 0:
        return f"данных нет: нужно минимум {minimum} проверенных LONG/SHORT"
    if count < 10:
        return f"очень мало данных: {count}/{minimum}; выводы нельзя делать"
    if count < minimum:
        return f"данных мало: {count}/{minimum}; нужно ещё {missing}"
    if count < minimum * 3:
        return f"выборка рабочая: {count}; выводы осторожные"
    return f"выборка сильная: {count}; можно сравнивать группы"


def sample_quality_badge(counted: Any, min_samples: int = 30) -> str:
    """Return a compact sample-size badge for menu cards."""
    try:
        count = max(0, int(counted))
    except (TypeError, ValueError):
        count = 0
    minimum = max(1, int(min_samples or 30))
    if count == 0:
        return "нет данных"
    if count < 10:
        return "очень мало"
    if count < minimum:
        return "мало"
    if count < minimum * 3:
        return "рабочая"
    return "сильная"


def basis_counts_text(wins: Any, losses: Any, flats: Any, pending: Any | None = None) -> str:
    """Explain which outcomes are counted in WR and which are tracked aside."""
    def to_int(value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    win_count = to_int(wins)
    loss_count = to_int(losses)
    flat_count = to_int(flats)
    parts = [
        f"WR база: {win_count + loss_count} WIN/LOSS",
        f"FLAT отдельно: {flat_count}",
    ]
    if pending is not None:
        parts.append(f"ждут: {to_int(pending)}")
    return " | ".join(parts)


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
