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
    return {
        "ts": event.get("ts"),
        "kind": "ENTRY" if event.get("kind") == "entry" else "PROTECT",
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
