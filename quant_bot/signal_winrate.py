"""Pure formatting helpers for signal Win Rate reports.

These helpers do not read or update the Win Rate journal. They only format
already-calculated values for Telegram cards.
"""
from __future__ import annotations

from datetime import datetime, timezone
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


def _focus_bucket_label(raw: dict[str, Any]) -> str:
    """Return a clear group-aware label for a Win Rate bucket."""
    label = str(raw.get("label") or "n/a")
    group = str(raw.get("group") or "").lower()
    prefix = {
        "ticker": "актив",
        "asset": "актив",
        "tf": "TF",
        "timeframe": "TF",
        "direction": "направление",
    }.get(group)
    if not prefix:
        return label
    return f"{prefix} {label}"


def focus_note_text(buckets: Any, min_samples: int = 5) -> str:
    """Return one short note about which Win Rate group deserves attention."""
    minimum = max(1, int(min_samples or 5))
    usable: list[dict[str, Any]] = []
    for raw in list(buckets or []):
        if not isinstance(raw, dict):
            continue
        try:
            counted = max(0, int(raw.get("counted") or 0))
        except (TypeError, ValueError):
            counted = 0
        if counted < minimum:
            continue
        try:
            winrate = float(raw.get("winrate"))
        except (TypeError, ValueError):
            continue
        try:
            edge = float(raw.get("avg_edge"))
        except (TypeError, ValueError):
            edge = 0.0
        usable.append({
            "label": _focus_bucket_label(raw),
            "counted": counted,
            "winrate": winrate,
            "edge": edge,
        })

    if not usable:
        return f"копим группы; для сравнения нужно минимум {minimum} WIN/LOSS в группе"

    best = max(usable, key=lambda x: (x["winrate"], x["edge"], x["counted"]))
    weak = min(usable, key=lambda x: (x["winrate"], x["edge"], -x["counted"]))

    parts: list[str] = []
    if best["winrate"] >= 60.0:
        parts.append(f"лучше: {best['label']} WR {best['winrate']:.1f}% ({best['counted']})")
    if weak["winrate"] <= 45.0 and (weak["label"] != best["label"] or not parts):
        parts.append(f"слабее: {weak['label']} WR {weak['winrate']:.1f}% ({weak['counted']})")
    if not parts:
        return "яркого перекоса нет; продолжай копить статистику по группам"
    return " | ".join(parts)


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


def _status_text(value: Any) -> str:
    """Extract an upper-case status from a raw status or journal row."""
    if isinstance(value, dict):
        value = value.get("status")
    return str(value or "").upper()


def recent_outcome_sequence(statuses: Any, limit: int = 8) -> str:
    """Build a compact newest-first sequence of recent Win Rate outcomes."""
    icon_map = {
        "WIN": "🟢W",
        "LOSS": "🔴L",
        "FLAT": "⚪F",
    }
    items: list[str] = []
    for value in list(statuses or [])[:max(1, int(limit or 8))]:
        token = icon_map.get(_status_text(value))
        if token:
            items.append(token)
    if not items:
        return "нет проверенных исходов"
    return " ".join(items)


def outcome_streak_text(statuses: Any) -> str:
    """Return the current same-outcome streak from newest-first statuses."""
    values = [_status_text(value) for value in list(statuses or [])]
    values = [value for value in values if value in {"WIN", "LOSS", "FLAT"}]
    if not values:
        return "серии нет"
    first = values[0]
    count = 0
    for value in values:
        if value != first:
            break
        count += 1
    return f"серия {first}: {count}"


def action_note_text(counted: Any, winrate: Any, statuses: Any, min_samples: int = 30) -> str:
    """Return a short, risk-first action note for current Win Rate evidence."""
    try:
        count = max(0, int(counted))
    except (TypeError, ValueError):
        count = 0
    minimum = max(1, int(min_samples or 30))
    values = [_status_text(value) for value in list(statuses or [])]
    values = [value for value in values if value in {"WIN", "LOSS", "FLAT"}]
    first = values[0] if values else ""
    streak = 0
    for value in values:
        if value != first:
            break
        streak += 1

    try:
        wr_value = float(winrate)
    except (TypeError, ValueError):
        wr_value = None

    if count < 10:
        return "копим данные; Win Rate пока не оценка качества"
    if first == "LOSS" and streak >= 3:
        return "серия LOSS; проверь последние идеи, но не меняй правила на эмоциях"
    if first == "WIN" and streak >= 5 and count < minimum:
        return "серия WIN приятная, но выборка мала; риск не повышать"
    if count < minimum:
        return f"продолжай сбор; до рабочей выборки ещё {minimum - count}"
    if wr_value is not None and wr_value >= 60:
        return "есть осторожное преимущество; сравнивай активы и TF"
    if wr_value is not None and wr_value <= 45:
        return "качество слабое; ищи фильтры по активам, TF и причинам LOSS"
    return "режим наблюдения; сравнивай группы без резких изменений"


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a journal datetime without depending on the legacy runtime."""
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def pending_check_text(rows: Any, now: datetime | None = None) -> str:
    """Explain when pending Win Rate signals will be checked next."""
    pending: list[datetime] = []
    for row in list(rows or []):
        if _status_text(row) != "PENDING":
            continue
        due = _parse_datetime(row.get("due_at") if isinstance(row, dict) else None)
        if due is not None:
            pending.append(due)
    if not pending:
        return "pending-сигналов нет"

    pending.sort()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    overdue = [dt for dt in pending if dt <= current]
    if overdue:
        return f"просрочены: {len(overdue)}; обнови Win Rate"
    return f"ближайшая проверка: {pending[0].strftime('%H:%M UTC')}"


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
