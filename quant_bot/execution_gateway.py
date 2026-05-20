"""Pure execution-gateway helpers.

These functions do not import the legacy bot. They are safe building blocks
that can gradually replace logic currently living in ``quant bot.py``.
"""
from __future__ import annotations

from typing import Any, Iterable


def truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "y"}


def format_decimal(value: Any, max_decimals: int = 8) -> str:
    try:
        number = float(value)
    except Exception:
        return "0"
    if number <= 0:
        return "0"
    return f"{number:.{int(max_decimals)}f}".rstrip("0").rstrip(".") or "0"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def format_execution_qty(value: Any) -> str:
    try:
        number = float(value)
        if number >= 100:
            return f"{number:.2f}"
        if number >= 1:
            return f"{number:.4f}"
        return f"{number:.6f}"
    except Exception:
        return "—"


def execution_plan_view(plan: dict[str, Any] | None) -> dict[str, Any]:
    plan = plan or {}
    order = plan.get("entry_order") or {}
    return {
        "created_at": plan.get("created_at"),
        "ticker": plan.get("ticker"),
        "interval": plan.get("interval"),
        "direction": str(plan.get("direction") or "").upper(),
        "status": plan.get("status") or "—",
        "quantity_text": format_execution_qty(order.get("quantity_est")),
        "notional": safe_float(order.get("notional_est"), 0.0),
    }


def response_reason(payload: Any) -> str:
    if isinstance(payload, dict):
        code = payload.get("code")
        msg = payload.get("msg") or payload.get("message")
        if code is not None and msg:
            return f"{code}: {msg}"
        if msg:
            return str(msg)
    return ""


def event_status(event: dict[str, Any] | None) -> str:
    event = event or {}
    if event.get("ok"):
        return "ACCEPTED"
    if event.get("submitted") is False or event.get("skipped"):
        return "SKIPPED"
    if event:
        return "REJECTED"
    return "MISSING"


def testnet_event_view(event: dict[str, Any] | None) -> dict[str, Any]:
    event = event or {}
    request = event.get("request") or {}
    kind_labels = {
        "entry": "ENTRY",
        "protection": "PROTECT",
        "real_entry": "REAL ENTRY",
        "real_protection": "REAL PROTECT",
        "real_emergency_close": "EMERGENCY CLOSE",
        "position_monitor": "POSITION MONITOR",
    }
    return {
        "ts": event.get("ts"),
        "kind": kind_labels.get(str(event.get("kind") or ""), str(event.get("kind") or "EVENT").upper()),
        "status": event_status(event),
        "ticker": event.get("ticker") or "?",
        "direction": str(event.get("direction") or "?").upper(),
        "type": request.get("type"),
        "side": request.get("side"),
        "quantity": request.get("quantity"),
        "stop_price": request.get("stopPrice"),
        "reason": event.get("reason"),
    }


def protection_status(event: dict[str, Any] | None) -> str:
    event = event or {}
    orders = list(event.get("orders") or [])
    if not orders:
        return event_status(event)
    if all(order.get("ok") for order in orders):
        return "ACCEPTED"
    if not any(order.get("submitted") for order in orders):
        return "SKIPPED"
    return "REJECTED"


def latest_event(events: Iterable[dict[str, Any]], kind: str) -> dict[str, Any] | None:
    matching = [event for event in events if event.get("kind") == kind or event.get("type") == kind]
    matching.sort(key=lambda event: str(event.get("ts") or ""), reverse=True)
    return matching[0] if matching else None


def protection_reason(event: dict[str, Any] | None) -> str:
    event = event or {}
    if event.get("reason"):
        return str(event["reason"])
    for order in event.get("orders") or []:
        if order.get("reason"):
            return f"{order.get('label')}: {order.get('reason')}"
        reason = response_reason(order.get("response"))
        if reason:
            return f"{order.get('label')}: {reason}"
    return response_reason(event.get("response"))


def planned_summary(plan: dict[str, Any] | None) -> dict[str, Any]:
    plan = plan or {}
    entry = plan.get("entry_order") or {}
    protection = []
    for order in plan.get("protection_orders") or []:
        protection.append({
            "label": order.get("label"),
            "side": order.get("side"),
            "type": order.get("type"),
            "stop_price": order.get("stop_price"),
            "reduce_only": order.get("reduce_only"),
        })
    return {
        "plan_id": plan.get("plan_id"),
        "ticker": plan.get("ticker"),
        "interval": plan.get("interval"),
        "direction": plan.get("direction"),
        "strategy": plan.get("strategy"),
        "entry_side": entry.get("side"),
        "quantity_est": entry.get("quantity_est"),
        "notional_est": entry.get("notional_est"),
        "entry_reference": entry.get("entry_reference"),
        "protection_orders": protection,
    }


def reconcile_testnet_plan(plan: dict[str, Any] | None, events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    event_list = list(events or [])
    entry = latest_event(event_list, "entry") or latest_event(event_list, "testnet_order_test")
    protection = latest_event(event_list, "protection") or latest_event(event_list, "testnet_protection_order_test")
    entry_status = event_status(entry)
    prot_status = protection_status(protection)
    if entry_status == "ACCEPTED" and prot_status == "ACCEPTED":
        overall = "ACCEPTED"
    elif "REJECTED" in {entry_status, prot_status}:
        overall = "REJECTED"
    elif entry_status == "MISSING" and prot_status == "MISSING":
        overall = "NO_TESTS"
    else:
        overall = "PARTIAL_OR_SKIPPED"
    reasons = []
    entry_reason = (entry or {}).get("reason") or response_reason((entry or {}).get("response"))
    prot_reason = protection_reason(protection)
    if entry_reason:
        reasons.append(f"entry: {entry_reason}")
    if prot_reason:
        reasons.append(f"protection: {prot_reason}")
    return {
        "overall": overall,
        "entry_status": entry_status,
        "protection_status": prot_status,
        "planned": planned_summary(plan),
        "entry_event": entry,
        "protection_event": protection,
        "reasons": reasons,
    }


def _as_list(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if payload is None:
        return []
    return [payload]


def _truthy_order_flag(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"} or value is True


def selected_position(position_payload: Any, symbol: str | None = None) -> dict[str, Any] | None:
    symbol_text = str(symbol or "").upper()
    for row in _as_list(position_payload):
        if not isinstance(row, dict):
            continue
        if symbol_text and str(row.get("symbol") or "").upper() != symbol_text:
            continue
        if abs(safe_float(row.get("positionAmt"), 0.0)) > 0:
            return row
    return None


def protection_orders(open_orders_payload: Any, plan: dict[str, Any] | None) -> dict[str, Any]:
    plan = plan or {}
    symbol = str(plan.get("api_symbol") or plan.get("ticker") or "").upper()
    direction = str(plan.get("direction") or "").lower()
    close_side = "SELL" if direction == "long" else ("BUY" if direction == "short" else "")
    orders = []
    sl_orders = []
    tp_orders = []
    bad_orders = []
    for row in _as_list(open_orders_payload):
        if not isinstance(row, dict):
            continue
        if symbol and str(row.get("symbol") or "").upper() != symbol:
            continue
        typ = str(row.get("type") or row.get("orderType") or "").upper()
        side = str(row.get("side") or "").upper()
        reduce_only = _truthy_order_flag(row.get("reduceOnly"))
        is_expected_side = not close_side or side == close_side
        if typ in {"STOP_MARKET", "STOP", "TAKE_PROFIT_MARKET", "TAKE_PROFIT"}:
            orders.append(row)
            if not reduce_only or not is_expected_side:
                bad_orders.append(row)
        if typ in {"STOP_MARKET", "STOP"} and reduce_only and is_expected_side:
            sl_orders.append(row)
        if typ in {"TAKE_PROFIT_MARKET", "TAKE_PROFIT"} and reduce_only and is_expected_side:
            tp_orders.append(row)
    return {
        "all": orders,
        "sl": sl_orders,
        "tp": tp_orders,
        "bad": bad_orders,
        "has_sl": bool(sl_orders),
        "tp_count": len(tp_orders),
        "has_tp": bool(tp_orders),
    }


def evaluate_position_monitor(
    plan: dict[str, Any] | None,
    position_payload: Any,
    open_orders_payload: Any,
) -> dict[str, Any]:
    plan = plan or {}
    symbol = plan.get("api_symbol") or plan.get("ticker")
    direction = str(plan.get("direction") or "").lower()
    entry_order = plan.get("entry_order") or {}
    planned_qty = safe_float(entry_order.get("quantity") or entry_order.get("quantity_est"), 0.0)
    position = selected_position(position_payload, symbol)
    protections = protection_orders(open_orders_payload, plan)
    blockers: list[str] = []
    warnings: list[str] = []

    if not position:
        if protections["all"]:
            status = "ORPHAN_ORDERS"
            blockers.append("position is closed but protective orders are still open")
        else:
            status = "NO_POSITION"
            warnings.append("Testnet position is not open or already closed")
        position_amt = 0.0
        direction_ok = None
    else:
        position_amt = safe_float(position.get("positionAmt"), 0.0)
        direction_ok = (direction == "long" and position_amt > 0) or (direction == "short" and position_amt < 0)
        if planned_qty > 0:
            qty_diff_pct = abs(abs(position_amt) - planned_qty) / planned_qty * 100.0
            if qty_diff_pct > 15.0:
                warnings.append("actual position size differs from planned size")
        if not direction_ok:
            blockers.append("position direction does not match the plan")
        if not protections["has_sl"]:
            blockers.append("missing reduceOnly STOP_MARKET SL")
        if not protections["has_tp"]:
            blockers.append("missing reduceOnly TAKE_PROFIT_MARKET TP")
        if protections["bad"]:
            blockers.append("some protective orders have wrong side or reduceOnly=false")
        if protections["has_tp"] and protections["tp_count"] < 2:
            warnings.append("only one take-profit order is visible")
        if blockers:
            status = "UNPROTECTED" if any("missing" in item for item in blockers) else "MISMATCH"
        else:
            status = "PROTECTED"

    return {
        "status": status,
        "ok": status in {"PROTECTED", "NO_POSITION"},
        "has_position": bool(position),
        "position_amt": position_amt,
        "position_side": "LONG" if position_amt > 0 else ("SHORT" if position_amt < 0 else "FLAT"),
        "position_qty_abs": abs(position_amt),
        "planned_qty": planned_qty,
        "qty_diff_pct": (abs(abs(position_amt) - planned_qty) / planned_qty * 100.0) if planned_qty > 0 else None,
        "entry_price": safe_float((position or {}).get("entryPrice"), 0.0),
        "mark_price": safe_float((position or {}).get("markPrice"), 0.0),
        "unrealized_pnl": safe_float((position or {}).get("unRealizedProfit"), 0.0),
        "direction_ok": direction_ok,
        "sl_count": len(protections["sl"]),
        "tp_count": protections["tp_count"],
        "bad_protection_count": len(protections["bad"]),
        "open_protection_count": len(protections["all"]),
        "orphan_order_count": len(protections["all"]) if not position else 0,
        "blockers": blockers,
        "warnings": warnings,
    }
