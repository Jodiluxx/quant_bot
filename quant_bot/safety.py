"""Pure safety helpers for gradual extraction from the legacy runtime."""
from __future__ import annotations

from typing import Any, Iterable


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def net_pnl(trades: Iterable[dict[str, Any]]) -> float:
    return sum(safe_float(trade.get("net_usd"), 0.0) for trade in trades or [])


def consecutive_losses(trades: Iterable[dict[str, Any]]) -> int:
    ordered = sorted(list(trades or []), key=lambda trade: str(trade.get("closed_at") or trade.get("opened_at") or ""), reverse=True)
    count = 0
    for trade in ordered:
        reason = str(trade.get("exit_reason") or "").upper()
        net = safe_float(trade.get("net_usd"), 0.0)
        if "SL" in reason or net < 0:
            count += 1
            continue
        break
    return count


def should_pause_after_losses(trades: Iterable[dict[str, Any]], threshold: int = 3) -> bool:
    return consecutive_losses(trades) >= int(threshold)
