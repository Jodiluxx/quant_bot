from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quant_bot.paper_trader import (
    data_quality_summary,
    directional_factors,
    positions_for_chat,
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


if __name__ == "__main__":
    unittest.main()
