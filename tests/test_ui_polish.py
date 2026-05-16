from __future__ import annotations

import unittest

from quant_bot.legacy import load_bot_module


class TelegramUiPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def test_main_keyboard_keeps_expected_callbacks(self) -> None:
        rows = self.bot.main_keyboard()["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        for callback in {
            "menu_signal",
            "menu_autobot",
            "menu_analytics",
            "menu_positions",
            "menu_settings",
            "menu_learn",
            "menu_flow",
            "get_fg",
            "get_price",
            "entry_point",
        }:
            self.assertIn(callback, callbacks)

    def test_autobot_keyboard_uses_existing_callbacks(self) -> None:
        rows = self.bot.autobot_keyboard(987654321)["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        for callback in {
            "paper_run_now",
            "paper_open_positions",
            "paper_closed_menu",
            "paper_report_autobot",
            "setup_analytics",
            "prob_calibration",
            "bot_quality",
            "execution_status",
            "safety_status",
            "market_opportunities",
            "performance_today",
            "live_readiness",
            "back_main",
        }:
            self.assertIn(callback, callbacks)

    def test_signal_card_is_compact_and_html_escapes_dynamic_text(self) -> None:
        text = self.bot.format_signal_summary(
            {
                "signal": "🟢 LONG",
                "direction": "long",
                "price": 100.0,
                "confidence": 81,
                "prob": 0.68,
                "strategy": "Pullback <test>",
                "bull_weight_sum": 8.0,
                "bear_weight_sum": 3.0,
                "vol_ratio": 1.4,
                "regime": "trend",
                "bull_args": ["Цена > EMA20"],
                "bear_args": ["Цена < EMA200"],
                "risk_levels": {"sl": 98.0, "tp1": 103.0, "tp2": 105.0, "rr_ratio": 1.7},
                "entry_plan": {
                    "status": "WAIT_RETEST",
                    "entry_now_score": 69,
                    "setup_score": 81,
                    "rr_now": 1.7,
                    "orderflow_state": "neutral",
                },
            },
            "BTCUSDT",
            "15m",
        )
        self.assertIn("📡 <b>BTCUSDT • LONG</b>", text)
        self.assertIn("WAIT RETEST", text)
        self.assertIn("Pullback &lt;test&gt;", text)
        self.assertIn("Цена &lt; EMA200", text)
        self.assertLessEqual(len(text.splitlines()), 32)

    def test_scan_rows_are_limited_and_readable(self) -> None:
        rows = [{"ticker": "ETHUSDT", "tf": "30m", "status": "WAIT_RETEST", "entry_now": n, "setup": n, "rr": 1.67} for n in range(10)]
        lines = self.bot._format_scan_rows(rows)
        self.assertEqual(len(lines), 5)
        self.assertIn("WAIT RETEST", lines[0])


if __name__ == "__main__":
    unittest.main()
