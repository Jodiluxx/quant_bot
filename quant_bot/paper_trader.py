"""Pure Paper Trader state helpers.

The legacy runtime still owns strategy decisions and Telegram rendering. These
helpers operate only on plain state dictionaries, so they are safe to test and
reuse while the big runtime is gradually split apart.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def chat_key(chat_id: Any) -> str:
    return str(chat_id)


def positions_for_chat(state: dict[str, Any], chat_id: Any = None) -> list[dict[str, Any]]:
    rows = list((state.get("positions") or {}).values())
    if chat_id is None:
        return rows
    key = chat_key(chat_id)
    return [row for row in rows if str(row.get("chat_id")) == key]


def closed_trades_for_chat(state: dict[str, Any], chat_id: Any = None) -> list[dict[str, Any]]:
    rows = list(state.get("trades") or [])
    if chat_id is None:
        return rows
    key = chat_key(chat_id)
    return [row for row in rows if str(row.get("chat_id")) == key]


def today_open_count(state: dict[str, Any], chat_id: Any, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(timezone.utc).date().isoformat()
    count = 0
    for trade in closed_trades_for_chat(state, chat_id):
        if str(trade.get("opened_at", "")).startswith(today):
            count += 1
    for pos in positions_for_chat(state, chat_id):
        if str(pos.get("opened_at", "")).startswith(today):
            count += 1
    return count


def interval_minutes(interval: Any, interval_meta: dict[str, Any] | None = None) -> int:
    interval_meta = interval_meta or {}
    meta = interval_meta.get(interval) or {}
    minutes = meta.get("minutes") if isinstance(meta, dict) else None
    if minutes:
        return max(1, int(minutes))
    text = str(interval or "").strip().lower()
    try:
        if text.endswith("m"):
            return max(1, int(text[:-1]))
        if text.endswith("h"):
            return max(1, int(text[:-1]) * 60)
        if text.endswith("d"):
            return max(1, int(text[:-1]) * 1440)
    except Exception:
        pass
    return 15


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def setup_slot(interval: Any, value: Any = None, interval_meta: dict[str, Any] | None = None) -> int:
    dt = parse_dt(value)
    seconds = interval_minutes(interval, interval_meta) * 60
    return int(dt.timestamp()) // max(seconds, 60)


def setup_family_id(item: dict[str, Any], chat_id: Any = None, interval_meta: dict[str, Any] | None = None) -> str:
    ticker = str(item.get("ticker") or "").upper()
    interval = str(item.get("interval") or item.get("tf") or "").lower()
    direction = str(item.get("direction") or "").lower()
    chat = chat_key(chat_id if chat_id is not None else item.get("chat_id"))
    slot = item.get("setup_slot") or setup_slot(interval, item.get("opened_at") or item.get("ts"), interval_meta)
    return f"paper_setup:{chat}:{ticker}:{interval}:{direction}:{int(slot)}"


def independent_setup_count(items: list[dict[str, Any]], interval_meta: dict[str, Any] | None = None) -> int:
    seen: set[str] = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        seen.add(str(item.get("setup_family_id") or setup_family_id(item, interval_meta=interval_meta)))
    return len(seen)


def independent_market_setup_count(items: list[dict[str, Any]], interval_meta: dict[str, Any] | None = None) -> int:
    seen: set[tuple[str, str, str, int]] = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        interval = str(item.get("interval") or item.get("tf") or "").lower()
        slot = item.get("setup_slot") or setup_slot(interval, item.get("opened_at") or item.get("ts"), interval_meta)
        seen.add((
            str(item.get("ticker") or "").upper(),
            interval,
            str(item.get("direction") or "").lower(),
            safe_int(slot),
        ))
    return len(seen)


def data_quality_summary(
    state: dict[str, Any],
    chat_id: Any = None,
    interval_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trades = closed_trades_for_chat(state, chat_id)
    positions = positions_for_chat(state, chat_id)
    closed_setups = independent_setup_count(trades, interval_meta)
    open_setups = independent_setup_count(positions, interval_meta)
    closed_market_setups = independent_market_setup_count(trades, interval_meta)
    open_market_setups = independent_market_setup_count(positions, interval_meta)
    return {
        "closed_trades": len(trades),
        "independent_closed_setups": closed_setups,
        "independent_market_closed_setups": closed_market_setups,
        "open_positions": len(positions),
        "independent_open_setups": open_setups,
        "independent_market_open_setups": open_market_setups,
        "closed_duplicate_rows": max(0, len(trades) - closed_setups),
        "open_duplicate_rows": max(0, len(positions) - open_setups),
        "market_closed_duplicate_rows": max(0, len(trades) - closed_market_setups),
        "market_open_duplicate_rows": max(0, len(positions) - open_market_setups),
        "data_quality_version": "v7.9",
    }


def short_text(value: Any, limit: int = 115) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= int(limit):
        return text
    return text[: max(0, int(limit) - 1)].rstrip() + "…"


def pnl_label(item: dict[str, Any]) -> str:
    net = safe_float(item.get("net_usd"), 0.0)
    pct = safe_float(item.get("net_pct_balance"), 0.0)
    icon = "✅" if net > 0 else ("❌" if net < 0 else "⚪")
    return f"{icon} {net:+.3f} USDT ({pct:+.2f}%)"


def exit_badge(item: dict[str, Any]) -> str:
    reason = str(item.get("exit_reason") or "closed").upper()
    if "TP" in reason:
        return "✅ TP1"
    if "SL" in reason:
        return "❌ SL"
    return f"⚪ {reason}"


def strategy_lines(trades: list[dict[str, Any]], limit: int = 4) -> list[str]:
    by_strategy: dict[str, dict[str, Any]] = {}
    for trade in trades or []:
        name = str(trade.get("strategy") or "unknown")
        row = by_strategy.setdefault(name, {"n": 0, "w": 0, "net": 0.0})
        row["n"] += 1
        net = safe_float(trade.get("net_usd"), 0.0)
        row["net"] += net
        row["w"] += 1 if net > 0 else 0
    lines: list[str] = []
    rows = sorted(by_strategy.items(), key=lambda kv: kv[1]["net"], reverse=True)
    for name, row in rows[: int(limit)]:
        wr = row["w"] / row["n"] * 100 if row["n"] else 0.0
        lines.append(f"• {name}: {row['n']} сдел. | WR {wr:.0f}% | {row['net']:+.3f} USDT")
    return lines


def directional_factors(item: dict[str, Any], limit: int = 95) -> tuple[list[str], list[str]]:
    decision = item.get("decision") or {}
    direction = str(item.get("direction") or "").lower()
    bull = [short_text(value, limit) for value in (decision.get("bull_factors") or []) if value]
    bear = [short_text(value, limit) for value in (decision.get("bear_factors") or []) if value]
    warnings = [short_text(value, limit) for value in (decision.get("warnings") or []) if value]
    if direction == "short":
        support = bear
        risks = bull + warnings
    elif direction == "long":
        support = bull
        risks = bear + warnings
    else:
        support = bull + bear
        risks = warnings
    return support[:2], risks[:2]
