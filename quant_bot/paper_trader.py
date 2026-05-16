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


def max_hold_minutes(
    interval: Any,
    configured: dict[str, int] | None = None,
    interval_meta: dict[str, Any] | None = None,
) -> int:
    configured = configured or {}
    key = str(interval)
    if key in configured:
        return int(configured[key])
    return interval_minutes(interval, interval_meta) * 24


def fill_price(price: Any, direction: Any, action: str, slippage_bps: float = 4.0) -> float:
    value = safe_float(price, 0.0)
    slip = safe_float(slippage_bps, 0.0) / 10000.0
    side = str(direction or "").lower()
    if action == "entry":
        return value * (1 + slip) if side == "long" else value * (1 - slip)
    return value * (1 - slip) if side == "long" else value * (1 + slip)


def breakeven_sl(entry: Any, direction: Any, buffer_bps: float = 0.0) -> float:
    value = safe_float(entry, 0.0)
    buffer = safe_float(buffer_bps, 0.0) / 10000.0
    if str(direction or "").lower() == "long":
        return value * (1 + buffer)
    return value * (1 - buffer)


def pnl_usd(direction: Any, entry: Any, exit_price: Any, notional: Any) -> float:
    entry_value = safe_float(entry, 0.0)
    exit_value = safe_float(exit_price, 0.0)
    size = safe_float(notional, 0.0)
    if entry_value <= 0 or exit_value <= 0 or size <= 0:
        return 0.0
    if str(direction or "").lower() == "long":
        pct = (exit_value - entry_value) / entry_value
    else:
        pct = (entry_value - exit_value) / entry_value
    return size * pct


def ensure_position_defaults(
    pos: dict[str, Any],
    *,
    fee_rate: float,
    slippage_bps: float,
    tp1_close_pct: float,
    max_hold: int,
) -> dict[str, Any]:
    notional = safe_float(pos.get("notional"), 0.0)
    if not pos.get("original_notional"):
        pos["original_notional"] = notional
    if not pos.get("remaining_notional"):
        pos["remaining_notional"] = notional
    if "entry_fee_usd" not in pos:
        pos["entry_fee_usd"] = notional * safe_float(fee_rate, 0.0)
    if "partials" not in pos or not isinstance(pos.get("partials"), list):
        pos["partials"] = []
    pos.setdefault("tp1_done", False)
    pos.setdefault("sl_original", pos.get("sl"))
    pos.setdefault("sl_current", pos.get("sl"))
    pos.setdefault("realism_version", "v7.26")
    pos.setdefault("slippage_bps", slippage_bps)
    pos.setdefault("tp1_close_pct", tp1_close_pct)
    pos.setdefault("max_hold_minutes", int(max_hold))
    return pos


def apply_partial_tp1(
    pos: dict[str, Any],
    market_price: Any,
    *,
    now: datetime | None = None,
    fee_rate: float,
    slippage_bps: float,
    tp1_close_pct: float,
    breakeven_buffer_bps: float,
) -> dict[str, Any] | None:
    if pos.get("tp1_done"):
        return None
    now = now or datetime.now(timezone.utc)
    direction = pos.get("direction")
    entry = safe_float(pos.get("entry_price"), 0.0)
    remaining = safe_float(pos.get("remaining_notional"), 0.0)
    original = safe_float(pos.get("original_notional"), 0.0) or remaining
    close_notional = min(remaining, original * safe_float(tp1_close_pct, 0.0) / 100.0)
    if entry <= 0 or close_notional <= 0:
        return None
    fill = fill_price(market_price, direction, "exit", slippage_bps)
    pnl = pnl_usd(direction, entry, fill, close_notional)
    exit_fee = close_notional * safe_float(fee_rate, 0.0)
    partial = {
        "type": "TP1_PARTIAL",
        "ts": now.astimezone(timezone.utc).isoformat(),
        "exit_price": fill,
        "market_price": market_price,
        "notional": close_notional,
        "pnl_usd": pnl,
        "fee_usd": exit_fee,
        "net_usd": pnl - exit_fee,
        "close_pct": tp1_close_pct,
    }
    pos.setdefault("partials", []).append(partial)
    pos["remaining_notional"] = max(0.0, remaining - close_notional)
    pos["tp1_done"] = True
    pos["tp1_hit_at"] = partial["ts"]
    pos["sl_before_be"] = pos.get("sl")
    pos["sl"] = breakeven_sl(entry, direction, breakeven_buffer_bps)
    pos["sl_current"] = pos["sl"]
    pos["breakeven_active"] = True
    return partial


def close_position_trade(
    pos: dict[str, Any],
    exit_price: Any,
    reason: str,
    *,
    now: datetime | None = None,
    fee_rate: float,
    default_balance: float,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    direction = pos.get("direction")
    entry = safe_float(pos.get("entry_price"), 0.0)
    original_notional = safe_float(pos.get("original_notional"), 0.0) or safe_float(pos.get("notional"), 0.0)
    remaining = safe_float(pos.get("remaining_notional"), 0.0) or original_notional
    partials = list(pos.get("partials") or [])
    partial_pnl = sum(safe_float(item.get("pnl_usd"), 0.0) for item in partials)
    partial_fees = sum(safe_float(item.get("fee_usd"), 0.0) for item in partials)
    final_pnl = pnl_usd(direction, entry, exit_price, remaining) if remaining > 0 else 0.0
    final_exit_fee = remaining * safe_float(fee_rate, 0.0)
    entry_fee = safe_float(pos.get("entry_fee_usd"), 0.0) or original_notional * safe_float(fee_rate, 0.0)
    pnl_total = partial_pnl + final_pnl
    fee_total = entry_fee + partial_fees + final_exit_fee
    net_usd = pnl_total - fee_total
    balance = safe_float(pos.get("balance"), default_balance) or default_balance
    trade = dict(pos)
    trade.update({
        "closed_at": now.astimezone(timezone.utc).isoformat(),
        "exit_price": exit_price,
        "exit_reason": reason,
        "pnl_pct": pnl_total / max(original_notional, 0.0001) * 100,
        "pnl_usd": pnl_total,
        "fee_usd": fee_total,
        "entry_fee_usd": entry_fee,
        "partial_fee_usd": partial_fees,
        "final_exit_fee_usd": final_exit_fee,
        "partial_pnl_usd": partial_pnl,
        "final_pnl_usd": final_pnl,
        "net_usd": net_usd,
        "net_pct_balance": net_usd / max(balance, 0.0001) * 100,
        "remaining_notional": 0.0,
        "closed_realism_version": "v7.26",
    })
    return trade


def price_exit_signal(pos: dict[str, Any], price: Any) -> str | None:
    value = safe_float(price, 0.0)
    direction = str(pos.get("direction") or "").lower()
    sl = safe_float(pos.get("sl"), 0.0)
    tp1 = safe_float(pos.get("tp1"), 0.0)
    tp2 = safe_float(pos.get("tp2"), tp1) or tp1
    tp1_done = bool(pos.get("tp1_done"))
    if direction == "long":
        if sl and value <= sl:
            return "SL_BE" if pos.get("breakeven_active") else "SL"
        if tp1_done and tp2 and value >= tp2:
            return "TP2"
        if not tp1_done and tp1 and value >= tp1:
            return "TP1_PARTIAL"
    else:
        if sl and value >= sl:
            return "SL_BE" if pos.get("breakeven_active") else "SL"
        if tp1_done and tp2 and value <= tp2:
            return "TP2"
        if not tp1_done and tp1 and value <= tp1:
            return "TP1_PARTIAL"
    return None


def hold_minutes(pos: dict[str, Any], now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    opened = parse_dt(pos.get("opened_at"))
    return max(0.0, (now.astimezone(timezone.utc) - opened).total_seconds() / 60.0)
