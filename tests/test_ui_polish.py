from __future__ import annotations

import asyncio

import unittest

from quant_bot.legacy import load_bot_module


class TelegramUiPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def test_main_keyboard_keeps_expected_callbacks(self) -> None:
        rows = self.bot.main_keyboard()["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        for callback in {"menu_signal", "menu_autobot", "auto_settings", "back_main"}:
            self.assertIn(callback, callbacks)
        for hidden in {"menu_analytics", "menu_positions", "menu_learn", "menu_flow", "get_fg", "entry_point"}:
            self.assertNotIn(hidden, callbacks)

    def test_autobot_keyboard_uses_existing_callbacks(self) -> None:
        rows = self.bot.autobot_keyboard(987654321)["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        for callback in {"paper_run_now", "paper_open_positions", "paper_closed_menu", "auto_settings", "back_main"}:
            self.assertIn(callback, callbacks)
        for hidden in {"setup_analytics", "prob_calibration", "bot_quality", "execution_status", "live_readiness"}:
            self.assertNotIn(hidden, callbacks)

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
        self.assertIn("📡 <b>BTCUSDT — WAIT</b>", text)
        self.assertIn("идея: <b>LONG</b>", text)
        self.assertIn("ждать ретест", text)
        self.assertIn("Цена &lt; EMA200", text)
        self.assertLessEqual(len(text.splitlines()), 28)

    def test_scan_rows_are_limited_and_readable(self) -> None:
        rows = [{"ticker": "ETHUSDT", "tf": "30m", "status": "WAIT_RETEST", "entry_now": n, "setup": n, "rr": 1.67} for n in range(10)]
        lines = self.bot._format_scan_rows(rows)
        self.assertEqual(len(lines), 5)
        self.assertIn("WAIT RETEST", lines[0])

    def test_simple_mode_blocks_hidden_old_callbacks(self) -> None:
        self.assertTrue(self.bot.simple_public_mode_enabled())
        for callback in {"menu_analytics", "execution_status", "sig_analysis", "market_heatmap"}:
            self.assertTrue(self.bot._simple_hidden_callback_v731(callback))
        for callback in {"menu_signal", "menu_autobot", "paper_run_now", "auto_settings"}:
            self.assertFalse(self.bot._simple_hidden_callback_v731(callback))

    def test_single_message_navigation_helpers_are_registered(self) -> None:
        self.assertEqual(self.bot.BOT_VERSION_LABEL, "v7.32 Single-Message Telegram Navigation")
        self.assertTrue(callable(self.bot.async_edit_message_text))
        self.assertTrue(callable(self.bot.send_or_edit))
        self.assertIn("async_edit_message_text", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("send_or_edit", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertTrue(any(layer[0] == "v7.32" for layer in self.bot.RUNTIME_LAYERS))

    def test_async_edit_message_text_uses_edit_endpoint(self) -> None:
        calls = []

        async def fake_api(session, method, payload=None):
            calls.append((method, payload or {}))
            return {"ok": True}

        old_api = self.bot.async_telegram_api
        self.bot.async_telegram_api = fake_api
        try:
            result = asyncio.run(self.bot.async_edit_message_text(
                object(),
                123,
                456,
                "<b>menu</b>",
                {"inline_keyboard": []},
            ))
        finally:
            self.bot.async_telegram_api = old_api

        self.assertTrue(result["ok"])
        self.assertEqual(calls[0][0], "editMessageText")
        self.assertEqual(calls[0][1]["chat_id"], 123)
        self.assertEqual(calls[0][1]["message_id"], 456)
        self.assertEqual(calls[0][1]["parse_mode"], "HTML")
        self.assertIn("reply_markup", calls[0][1])


if __name__ == "__main__":
    unittest.main()
