from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quant_bot.paper_trader import (
    apply_partial_tp1,
    close_position_trade,
    data_quality_summary,
    directional_factors,
    fill_price,
    positions_for_chat,
    price_exit_signal,
    today_open_count,
)


class PaperTraderStateTests(unittest.TestCase):
    def test_filters_positions_and_counts_daily_entries(self) -> None:
        state = {
            "positions": {
                "p1": {"chat_id": "1", "ticker": "BTCUSDT", "interval": "15m", "direction": "long", "opened_at": "2026-05-16T01:00:00+00:00"},
                "p2": {"chat_id": "2", "ticker": "ETHUSDT", "interval": "15m", "direction": "short", "opened_at": "2026-05-16T01:00:00+00:00"},
            },
            "trades": [
                {"chat_id": "1", "ticker": "BTCUSDT", "interval": "15m", "direction": "long", "opened_at": "2026-05-16T00:00:00+00:00"},
                {"chat_id": "1", "ticker": "SOLUSDT", "interval": "30m", "direction": "short", "opened_at": "2026-05-15T00:00:00+00:00"},
            ],
        }
        self.assertEqual(len(positions_for_chat(state, "1")), 1)
        self.assertEqual(today_open_count(state, "1", datetime(2026, 5, 16, tzinfo=timezone.utc)), 2)

    def test_data_quality_counts_independent_market_setups(self) -> None:
        state = {
            "positions": {},
            "trades": [
                {"chat_id": "1", "ticker": "BTCUSDT", "interval": "15m", "direction": "long", "opened_at": "2026-05-16T00:00:00+00:00"},
                {"chat_id": "2", "ticker": "BTCUSDT", "interval": "15m", "direction": "long", "opened_at": "2026-05-16T00:05:00+00:00"},
                {"chat_id": "1", "ticker": "ETHUSDT", "interval": "30m", "direction": "short", "opened_at": "2026-05-16T00:00:00+00:00"},
            ],
        }
        summary = data_quality_summary(state, None)
        self.assertEqual(summary["closed_trades"], 3)
        self.assertEqual(summary["independent_market_closed_setups"], 2)
        self.assertEqual(summary["market_closed_duplicate_rows"], 1)

    def test_directional_factors_flip_for_short(self) -> None:
        item = {
            "direction": "short",
            "decision": {
                "bull_factors": ["price above ema"],
                "bear_factors": ["lower low"],
                "warnings": ["low volume"],
            },
        }
        support, risks = directional_factors(item)
        self.assertEqual(support, ["lower low"])
        self.assertEqual(risks, ["price above ema", "low volume"])

    def test_fill_price_applies_worse_execution(self) -> None:
        self.assertAlmostEqual(fill_price(100, "long", "entry", 10), 100.1)
        self.assertAlmostEqual(fill_price(100, "long", "exit", 10), 99.9)
        self.assertAlmostEqual(fill_price(100, "short", "entry", 10), 99.9)
        self.assertAlmostEqual(fill_price(100, "short", "exit", 10), 100.1)

    def test_partial_tp1_moves_stop_to_break_even(self) -> None:
        pos = {
            "direction": "long",
            "entry_price": 100.0,
            "sl": 95.0,
            "remaining_notional": 100.0,
            "original_notional": 100.0,
            "partials": [],
        }
        partial = apply_partial_tp1(
            pos,
            110.0,
            now=datetime(2026, 5, 16, tzinfo=timezone.utc),
            fee_rate=0.001,
            slippage_bps=0.0,
            tp1_close_pct=50.0,
            breakeven_buffer_bps=0.0,
        )
        self.assertIsNotNone(partial)
        self.assertTrue(pos["tp1_done"])
        self.assertEqual(pos["remaining_notional"], 50.0)
        self.assertEqual(pos["sl"], 100.0)

    def test_price_exit_signal_understands_tp1_and_be_stop(self) -> None:
        pos = {"direction": "long", "sl": 95, "tp1": 110, "tp2": 120, "tp1_done": False}
        self.assertEqual(price_exit_signal(pos, 111), "TP1_PARTIAL")
        pos.update({"tp1_done": True, "breakeven_active": True, "sl": 100})
        self.assertEqual(price_exit_signal(pos, 99), "SL_BE")

    def test_close_position_trade_combines_partial_and_final_pnl(self) -> None:
        pos = {
            "direction": "long",
            "entry_price": 100.0,
            "original_notional": 100.0,
            "remaining_notional": 50.0,
            "entry_fee_usd": 0.1,
            "balance": 1000.0,
            "partials": [{"pnl_usd": 5.0, "fee_usd": 0.05}],
        }
        trade = close_position_trade(
            pos,
            120.0,
            "TP2",
            now=datetime(2026, 5, 16, tzinfo=timezone.utc),
            fee_rate=0.001,
            default_balance=1000.0,
        )
        self.assertAlmostEqual(trade["pnl_usd"], 15.0)
        self.assertAlmostEqual(trade["fee_usd"], 0.2)
        self.assertAlmostEqual(trade["net_usd"], 14.8)


if __name__ == "__main__":
    unittest.main()
