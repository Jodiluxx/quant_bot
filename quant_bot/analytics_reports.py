"""Pure analytics report helpers for gradual extraction from the legacy runtime."""
from __future__ import annotations

from typing import Any, Callable, Iterable


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def profit_factor(values: Iterable[float]) -> float | None:
    vals = [float(v) for v in values or []]
    gross_win = sum(v for v in vals if v > 0)
    gross_loss = abs(sum(v for v in vals if v < 0))
    if gross_loss <= 0:
        return None if gross_win <= 0 else float("inf")
    return gross_win / gross_loss


def average(values: Iterable[float]) -> float | None:
    vals = [float(v) for v in values or []]
    return sum(vals) / len(vals) if vals else None


def group_items(items: Iterable[dict[str, Any]], key_fn: Callable[[dict[str, Any]], str]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items or []:
        key = key_fn(item) or "unknown"
        grouped.setdefault(str(key), []).append(item)
    return grouped
