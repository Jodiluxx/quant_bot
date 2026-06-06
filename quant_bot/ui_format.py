"""Small Telegram UI formatting helpers.

These helpers are intentionally pure: no Telegram API calls, no trading logic,
and no project state. The legacy bot can call them while UI code is migrated
out of the monolith in small, testable steps.
"""
from __future__ import annotations


def clamp_score(value: object, default: float = 0.0) -> float:
    """Return a 0..100 float for UI scores."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = float(default)
    return max(0.0, min(100.0, score))


def score_bar(value: object, width: int = 10) -> str:
    """Visual score bar for 0..100 values."""
    score = clamp_score(value)
    width = max(4, int(width))
    filled = max(0, min(width, int(round(score / 100.0 * width))))
    if score >= 75:
        block = "🟩"
    elif score >= 50:
        block = "🟨"
    else:
        block = "🟥"
    return block * filled + "⬜" * (width - filled)


def winrate_bar(winrate: object, width: int = 8) -> str:
    """Compact winrate bar. Unknown values render as an empty bar."""
    width = max(4, int(width))
    if winrate is None:
        return "⬜" * width
    score = clamp_score(winrate)
    filled = max(0, min(width, int(round(score / 100.0 * width))))
    return "🟩" * filled + "⬜" * (width - filled)


def edge_text(value: object, unknown: str = "⚪ н/д") -> str:
    """Human-readable average edge in percent."""
    if value is None:
        return unknown
    try:
        edge = float(value)
    except (TypeError, ValueError):
        return unknown
    icon = "🟢" if edge > 0 else "🔴" if edge < 0 else "⚪"
    return f"{icon} {edge:+.2f}%"
