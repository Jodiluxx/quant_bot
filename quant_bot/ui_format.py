"""Small Telegram UI formatting helpers.

These helpers are intentionally pure: no Telegram API calls, no trading logic,
and no project state. The legacy bot can call them while UI code is migrated
out of the monolith in small, testable steps.
"""
from __future__ import annotations


RULE = "───────────────────"


def html_escape(value: object) -> str:
    """Escape dynamic text for Telegram HTML parse mode."""
    text = str(value or "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def short_text(value: object, limit: int = 96) -> str:
    """One-line, Telegram-safe shortened text."""
    text = " ".join(str(value or "").replace("\n", " ").split())
    limit = int(limit)
    if len(text) <= limit:
        return html_escape(text)
    return html_escape(text[: max(0, limit - 1)].rstrip() + "…")


def code(value: object) -> str:
    """Telegram HTML code wrapper with escaping."""
    return f"<code>{html_escape(value)}</code>"


def compact_tf(interval: object, fallback_label: object | None = None) -> str:
    """Compact timeframe label for Telegram buttons and cards."""
    text = str(interval or "")
    if text.endswith("m") and text[:-1].isdigit():
        return text[:-1] + "м"
    if text.endswith("h") and text[:-1].isdigit():
        return text[:-1] + "ч"
    if text.endswith("d") and text[:-1].isdigit():
        return text[:-1] + "д"
    label = str(fallback_label if fallback_label is not None else text)
    return (
        label.replace(" минут", "м")
        .replace(" минута", "м")
        .replace(" мин", "м")
        .replace(" часа", "ч")
        .replace(" час", "ч")
    )


def status_plain(status: object) -> str:
    """Normalize internal setup statuses for user-facing cards."""
    raw = str(status or "").upper()
    return {
        "ENTER_NOW": "READY",
        "WAIT_RETEST": "WAIT RETEST",
        "WAIT_CONFIRMATION": "WAIT CONFIRM",
        "NO_ENTRY": "BLOCKED",
        "NO_SETUP": "WAIT",
        "TP1_PARTIAL": "TP1",
        "SL_BE": "BE STOP",
    }.get(raw, str(status or "WAIT").replace("_", " "))


def status_emoji(status: object) -> str:
    """Status label with one clear emoji."""
    plain = status_plain(status)
    if plain == "READY":
        return "🟢 READY"
    if plain.startswith("WAIT"):
        return "🟡 " + plain
    if plain == "BLOCKED":
        return "🔴 BLOCKED"
    return "⚪ " + plain


def status_human(status: object) -> str:
    """Human wording for signal detail cards."""
    plain = status_plain(status)
    return {
        "READY": "READY",
        "WAIT RETEST": "WAIT: ожидание ретеста",
        "WAIT CONFIRM": "WAIT: нужно подтверждение",
        "BLOCKED": "BLOCKED",
        "WAIT": "WAIT",
    }.get(plain, plain)


def scan_status(decision: object) -> str:
    """Compact status marker for all-asset scan rows."""
    text = str(decision or "WAIT").upper()
    if text == "LONG":
        return "🟢 LONG"
    if text == "SHORT":
        return "🔴 SHORT"
    if text == "ERROR":
        return "⚪ ERROR"
    return "🟡 WAIT"


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
