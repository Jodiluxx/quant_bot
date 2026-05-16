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


def probability_value(value: Any) -> float | None:
    """Normalize a stored probability to 0..1.

    The legacy bot sometimes stores probabilities as 68 and sometimes as 0.68.
    Report calculations should treat both as the same forecast.
    """
    try:
        probability = float(value)
    except Exception:
        return None
    if probability > 1.0:
        probability /= 100.0
    if probability < 0.0 or probability > 1.0:
        return None
    return probability


def probability_bucket(probability: Any, step: int = 5) -> str:
    value = probability_value(probability)
    if value is None:
        return "unknown"
    width = max(1, int(step))
    pct = value * 100.0
    lo = int(pct // width) * width
    hi = lo + width
    return f"{lo}-{hi}%"


def calibration_stats(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    clean_rows: list[dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        probability = probability_value(row.get("prob"))
        if probability is None:
            continue
        clean = dict(row)
        clean["prob"] = probability
        clean_rows.append(clean)

    binary = [row for row in clean_rows if row.get("outcome") in {"win", "loss"}]
    if not binary:
        return {
            "n": len(clean_rows),
            "binary_n": 0,
            "neutral": len(clean_rows),
            "avg_prob": None,
            "actual_wr": None,
            "gap": None,
            "brier": None,
            "ece": None,
        }

    avg_prob = sum(row["prob"] for row in binary) / len(binary)
    actual_wr = sum(1 for row in binary if row.get("outcome") == "win") / len(binary)
    brier = sum(
        (row["prob"] - (1.0 if row.get("outcome") == "win" else 0.0)) ** 2
        for row in binary
    ) / len(binary)
    return {
        "n": len(clean_rows),
        "binary_n": len(binary),
        "neutral": len(clean_rows) - len(binary),
        "avg_prob": avg_prob,
        "actual_wr": actual_wr,
        "gap": actual_wr - avg_prob,
        "brier": brier,
        "ece": None,
    }


def calibration_group(
    rows: Iterable[dict[str, Any]],
    key_fn: Callable[[dict[str, Any]], Any],
    min_n: int = 20,
) -> tuple[list[tuple[str, dict[str, Any]]], float | None]:
    groups = group_items(rows, lambda row: str(key_fn(row) or "unknown"))
    out: list[tuple[str, dict[str, Any]]] = []
    total_binary = 0
    weighted_abs_gap = 0.0

    for key, items in groups.items():
        stats = calibration_stats(items)
        binary_n = int(stats.get("binary_n") or 0)
        total_binary += binary_n
        if binary_n < int(min_n):
            continue
        weighted_abs_gap += abs(float(stats.get("gap") or 0.0)) * binary_n
        out.append((key, stats))

    ece = weighted_abs_gap / total_binary if total_binary else None
    out.sort(key=lambda item: item[0])
    return out, ece
