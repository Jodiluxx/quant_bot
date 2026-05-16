"""Migration checklist helpers for the legacy-to-package split."""
from __future__ import annotations

from typing import Any


MIGRATION_AREAS: list[dict[str, Any]] = [
    {
        "area": "Runtime facade",
        "status": "done",
        "modules": ["quant_bot.runtime", "quant_bot.legacy", "quant_bot.adapters.*"],
        "legacy": "entrypoint still loads quant bot.py",
        "next": "keep adapters thin while moving implementations",
        "risk": "low",
    },
    {
        "area": "Execution gateway",
        "status": "partial",
        "modules": ["quant_bot.execution_gateway"],
        "legacy": "order-plan creation, signed Testnet calls and state journal still in quant bot.py",
        "next": "move request builders and journal state after tests cover them",
        "risk": "medium",
    },
    {
        "area": "Safety / kill switch",
        "status": "partial",
        "modules": ["quant_bot.safety"],
        "legacy": "manual pause state, observe-only routing and Telegram controls still in quant bot.py",
        "next": "extract safety state store and command handlers",
        "risk": "medium",
    },
    {
        "area": "Analytics reports",
        "status": "partial",
        "modules": ["quant_bot.analytics_reports"],
        "legacy": "bot quality, setup analytics, calibration and period reports still mostly in quant bot.py",
        "next": "move calculation functions before moving Telegram formatting",
        "risk": "medium",
    },
    {
        "area": "Live readiness",
        "status": "done",
        "modules": ["quant_bot.live_readiness"],
        "legacy": "legacy runtime gathers live paper/testnet/safety data",
        "next": "keep as gate before Testnet real execution",
        "risk": "low",
    },
    {
        "area": "Paper Trader state",
        "status": "done",
        "modules": ["quant_bot.paper_trader"],
        "legacy": "legacy runtime still owns file IO and position mutation",
        "next": "move state store after duplicate guard tests are stronger",
        "risk": "low",
    },
    {
        "area": "Paper Trader engine",
        "status": "partial",
        "modules": ["quant_bot.paper_trader"],
        "legacy": "candidate selection, opening side effects, price fetching and state mutation still remain in quant bot.py",
        "next": "extract candidate scoring and a state-store boundary after more tests",
        "risk": "high",
    },
    {
        "area": "Telegram UI",
        "status": "pending",
        "modules": [],
        "legacy": "menus, callback routing and keyboards remain in quant bot.py",
        "next": "move keyboards first, then callback routing by menu group",
        "risk": "medium",
    },
    {
        "area": "Backtest / WFO",
        "status": "pending",
        "modules": [],
        "legacy": "backtest and walk-forward implementation remain in quant bot.py",
        "next": "extract pure trade simulation and WFO windowing",
        "risk": "medium",
    },
    {
        "area": "Market data",
        "status": "pending",
        "modules": [],
        "legacy": "Binance OHLCV, cache and websocket handling remain in quant bot.py",
        "next": "extract REST client after cache tests exist",
        "risk": "medium",
    },
]


def migration_summary(areas: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = list(areas or MIGRATION_AREAS)
    by_status = {"done": 0, "partial": 0, "pending": 0}
    for row in rows:
        status = str(row.get("status") or "pending")
        by_status[status] = by_status.get(status, 0) + 1
    total = len(rows)
    progress = (by_status.get("done", 0) + by_status.get("partial", 0) * 0.5) / total * 100 if total else 0.0
    return {
        "total": total,
        "done": by_status.get("done", 0),
        "partial": by_status.get("partial", 0),
        "pending": by_status.get("pending", 0),
        "progress": round(progress, 1),
    }


def migration_next_steps(areas: list[dict[str, Any]] | None = None, limit: int = 5) -> list[str]:
    rows = list(areas or MIGRATION_AREAS)
    priority = {"high": 0, "medium": 1, "low": 2}
    candidates = [row for row in rows if row.get("status") != "done"]
    candidates.sort(key=lambda row: (priority.get(str(row.get("risk") or "medium"), 1), str(row.get("area"))))
    return [f"{row['area']}: {row.get('next')}" for row in candidates[: int(limit)]]


def checklist_payload(runtime_version: str, runtime_layers: list[tuple[str, str]], active_functions: dict[str, Any]) -> dict[str, Any]:
    summary = migration_summary()
    return {
        "runtime_version": runtime_version,
        "runtime_layers": len(runtime_layers or []),
        "active_functions": len(active_functions or {}),
        "summary": summary,
        "areas": list(MIGRATION_AREAS),
        "next_steps": migration_next_steps(),
    }
