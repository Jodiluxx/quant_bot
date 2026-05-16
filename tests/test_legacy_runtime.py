from __future__ import annotations

import unittest

from quant_bot.legacy import load_bot_module


class LegacyRuntimeSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def test_runtime_architecture_validates(self) -> None:
        self.assertTrue(self.bot.validate_runtime_architecture())

    def test_protection_geometry_rejects_wrong_long_sl(self) -> None:
        plan = {
            "direction": "long",
            "entry_order": {"entry_reference": 100},
            "protection_orders": [
                {"label": "SL", "side": "SELL", "type": "STOP_MARKET", "stop_price": 101, "reduce_only": True},
                {"label": "TP1", "side": "SELL", "type": "TAKE_PROFIT_MARKET", "stop_price": 110, "reduce_only": True},
            ],
        }
        result = self.bot.validate_protection_order_geometry(plan)
        self.assertFalse(result["ok"])
        self.assertTrue(any("LONG SL" in item for item in result["blockers"]))

    def test_probability_calibration_stats(self) -> None:
        rows = [
            {"prob": 0.7, "outcome": "win"},
            {"prob": 0.7, "outcome": "loss"},
            {"prob": 0.6, "outcome": "neutral"},
        ]
        stats = self.bot._calibration_stats_v712(rows)
        self.assertEqual(stats["binary_n"], 2)
        self.assertEqual(stats["neutral"], 1)
        self.assertAlmostEqual(stats["actual_wr"], 0.5)


if __name__ == "__main__":
    unittest.main()
