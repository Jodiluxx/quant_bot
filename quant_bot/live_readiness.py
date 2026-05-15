"""Pure live-readiness checklist helpers.

This module intentionally does not enable live trading. It only evaluates
whether the bot has enough evidence and safety controls to discuss the next
stage.
"""
from __future__ import annotations

from typing import Any, Iterable


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


def check_item(
    key: str,
    title: str,
    ok: bool,
    value: Any,
    target: Any,
    detail: str = "",
    *,
    hard_block: bool = True,
) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "ok": bool(ok),
        "value": value,
        "target": target,
        "detail": detail,
        "hard_block": bool(hard_block),
    }


def summarize_reconciliations(reconciliations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(reconciliations or [])
    accepted = sum(1 for row in rows if row.get("overall") == "ACCEPTED")
    rejected = sum(1 for row in rows if row.get("overall") == "REJECTED")
    skipped = sum(1 for row in rows if row.get("overall") in {"PARTIAL_OR_SKIPPED", "NO_TESTS"})
    total = len(rows)
    reject_rate = (rejected / total * 100.0) if total else 0.0
    return {
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
        "skipped": skipped,
        "reject_rate": reject_rate,
    }


def setup_coverage(trades: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in trades or [] if isinstance(row, dict)]
    tickers = {str(row.get("ticker") or "").upper() for row in rows if row.get("ticker")}
    intervals = {str(row.get("interval") or "").lower() for row in rows if row.get("interval")}
    strategies = {str(row.get("strategy") or "unknown") for row in rows}
    groups = {
        (
            str(row.get("ticker") or "").upper(),
            str(row.get("interval") or "").lower(),
            str(row.get("strategy") or "unknown"),
        )
        for row in rows
    }
    groups.discard(("", "", "unknown"))
    return {
        "tickers": len(tickers),
        "intervals": len(intervals),
        "strategies": len(strategies),
        "groups": len(groups),
    }


def evaluate_live_readiness(metrics: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    paper_trades = safe_int(metrics.get("paper_closed_trades"))
    independent = safe_int(metrics.get("paper_independent_setups"))
    market_setups = safe_int(metrics.get("paper_market_setups"))
    profit_factor = metrics.get("paper_profit_factor")
    avg_r = metrics.get("paper_avg_r")
    testnet_total = safe_int(metrics.get("testnet_total"))
    testnet_accepted = safe_int(metrics.get("testnet_accepted"))
    reject_rate = safe_float(metrics.get("testnet_reject_rate"))
    daily_loss_limit = safe_float(metrics.get("daily_loss_limit_pct"))
    max_daily_trades = safe_int(metrics.get("max_daily_trades"))
    max_open_positions = safe_int(metrics.get("max_open_positions"))
    setup_groups = safe_int(metrics.get("setup_groups"))
    setup_tickers = safe_int(metrics.get("setup_tickers"))
    setup_intervals = safe_int(metrics.get("setup_intervals"))
    setup_strategies = safe_int(metrics.get("setup_strategies"))

    min_pf = safe_float(thresholds.get("min_profit_factor"), 1.2)
    min_avg_r = safe_float(thresholds.get("min_avg_r"), 0.0)
    pf_ok = profit_factor is not None and safe_float(profit_factor) >= min_pf
    avg_r_ok = avg_r is not None and safe_float(avg_r) > min_avg_r

    checks = [
        check_item(
            "paper_trades",
            "Paper-сделок достаточно",
            paper_trades >= safe_int(thresholds.get("min_paper_trades"), 100),
            paper_trades,
            thresholds.get("min_paper_trades"),
            "Мало сделок легко дают случайную красивую статистику.",
        ),
        check_item(
            "independent_setups",
            "Независимых setup достаточно",
            independent >= safe_int(thresholds.get("min_independent_setups"), 80),
            independent,
            thresholds.get("min_independent_setups"),
            "Повторы одной идеи не считаются полноценной статистикой.",
        ),
        check_item(
            "market_setups",
            "Рыночных setup достаточно",
            market_setups >= safe_int(thresholds.get("min_market_setups"), 100),
            market_setups,
            thresholds.get("min_market_setups"),
            "Нужно видеть поведение бота на разных активах и режимах рынка.",
        ),
        check_item(
            "paper_profit_factor",
            "Profit Factor не слабый",
            pf_ok,
            "n/a" if profit_factor is None else f"{safe_float(profit_factor):.2f}",
            f">= {min_pf:.2f}",
            "PF ниже порога означает, что прибыль не перекрывает убытки с запасом.",
        ),
        check_item(
            "paper_avg_r",
            "Средний результат в R положительный",
            avg_r_ok,
            "n/a" if avg_r is None else f"{safe_float(avg_r):+.2f}R",
            f"> {min_avg_r:.2f}R",
            "R показывает результат относительно риска, а не размера позиции.",
        ),
        check_item(
            "testnet_total",
            "Testnet-сверок достаточно",
            testnet_total >= safe_int(thresholds.get("min_testnet_reconciliations"), 25),
            testnet_total,
            thresholds.get("min_testnet_reconciliations"),
            "Нужно проверить не только входы, но и защитные SL/TP.",
        ),
        check_item(
            "testnet_accepted",
            "Testnet принимает планы",
            testnet_accepted >= safe_int(thresholds.get("min_testnet_accepted"), 20),
            testnet_accepted,
            thresholds.get("min_testnet_accepted"),
            "Если биржа часто отклоняет параметры, live обсуждать рано.",
        ),
        check_item(
            "testnet_reject_rate",
            "Доля отказов Testnet приемлемая",
            reject_rate <= safe_float(thresholds.get("max_testnet_reject_rate"), 20.0) and testnet_total > 0,
            f"{reject_rate:.1f}%",
            f"<= {safe_float(thresholds.get('max_testnet_reject_rate'), 20.0):.1f}%",
            "Высокая доля отказов значит, что исполнение ещё не надёжно.",
        ),
        check_item(
            "daily_loss_limit",
            "Дневной лимит убытка задан",
            0.0 < daily_loss_limit <= safe_float(thresholds.get("max_daily_loss_limit_pct"), 3.0),
            f"{daily_loss_limit:.2f}%",
            f"0..{safe_float(thresholds.get('max_daily_loss_limit_pct'), 3.0):.2f}%",
            "Без дневного стопа серия ошибок может быстро уничтожить депозит.",
        ),
        check_item(
            "kill_switch",
            "Kill switch доступен",
            bool(metrics.get("kill_switch_configured")),
            "есть" if metrics.get("kill_switch_configured") else "нет",
            "есть",
            "Нужен механизм, который запрещает новые входы при плохом состоянии.",
        ),
        check_item(
            "position_limits",
            "Лимиты частоты и позиций заданы",
            max_daily_trades > 0 and max_open_positions > 0,
            f"{max_daily_trades}/день, {max_open_positions} открытых",
            "> 0",
            "Бот не должен открывать бесконечное число сделок.",
        ),
        check_item(
            "setup_stats",
            "Setup-статистика есть",
            setup_groups >= safe_int(thresholds.get("min_setup_groups"), 3)
            and setup_tickers >= 2
            and setup_intervals >= 2
            and setup_strategies >= 1,
            f"{setup_groups} групп, {setup_tickers} тикеров, {setup_intervals} TF, {setup_strategies} стратегий",
            f">= {thresholds.get('min_setup_groups')} групп + разные рынки",
            "Иначе непонятно, где бот реально силён, а где просто повезло.",
        ),
        check_item(
            "live_blocked_by_code",
            "Live/mainnet заблокирован кодом",
            not bool(metrics.get("live_orders_enabled")),
            "OFF" if not metrics.get("live_orders_enabled") else "ON",
            "OFF",
            "Это защита: чеклист не является кнопкой запуска live.",
            hard_block=False,
        ),
    ]

    hard_blockers = [item for item in checks if not item["ok"] and item["hard_block"]]
    warnings = [item for item in checks if not item["ok"] and not item["hard_block"]]
    ok_count = sum(1 for item in checks if item["ok"])
    score = round(ok_count / len(checks) * 100.0, 1) if checks else 0.0
    if hard_blockers:
        status = "BLOCKED"
    elif warnings:
        status = "WATCH"
    else:
        status = "READY_TO_DISCUSS"
    return {
        "status": status,
        "score": score,
        "checks": checks,
        "blockers": [item["title"] for item in hard_blockers],
        "warnings": [item["title"] for item in warnings],
    }
