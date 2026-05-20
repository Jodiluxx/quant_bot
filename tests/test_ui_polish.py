from __future__ import annotations

import asyncio
import os
import tempfile

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
        self.assertEqual(self.bot.BOT_VERSION_LABEL, "v7.43 Testnet Fill Quality + Orphan Cleanup")
        self.assertTrue(callable(self.bot.async_edit_message_text))
        self.assertTrue(callable(self.bot.send_or_edit))
        self.assertIn("async_edit_message_text", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("send_or_edit", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertTrue(any(layer[0] == "v7.32" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.33" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.34" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.35" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.36" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.37" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.38" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.39" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.40" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.41" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.42" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.43" for layer in self.bot.RUNTIME_LAYERS))
        self.assertIn("testnet_select_trade_candidate", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("demo_analysis_record_cycle", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("run_immediate_testnet_monitor", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_public_stats", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("normalize_testnet_plan", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_connection_status", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("rebuild_testnet_lifecycle", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("cancel_testnet_open_orders", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("cancel_testnet_algo_orders", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_auto_safety_after_monitor", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("submit_testnet_emergency_close_position", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_closed_trade_rows", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_pnl_attribution", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_position_quality", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("submit_testnet_trade", self.bot.ACTIVE_RUNTIME_FUNCTIONS)

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

    def test_testnet_status_line_distinguishes_paper_from_exchange(self) -> None:
        line = self.bot._testnet_position_status_line_v733({
            "testnet_real_order": {
                "entry": {
                    "submitted": False,
                    "ok": False,
                    "reason": "entry <blocked>",
                }
            }
        })
        self.assertIn("ордер не отправлен", line)
        self.assertIn("entry &lt;blocked&gt;", line)

    def test_testnet_only_menu_hides_paper_language(self) -> None:
        text = self.bot.format_autobot_menu(987654321)
        self.assertIn("Binance Testnet", text)
        self.assertIn("Binance:", text)
        self.assertNotIn("Paper-", text)
        self.assertNotIn("paper-", text)
        self.assertNotIn("Paper Trader", text)

    def test_testnet_gate_does_not_use_stale_paper_positions(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_count = self.bot._testnet_today_real_entry_count_v734
        old_plan = self.bot._build_testnet_trade_plan_v734
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_today_real_entry_count_v734 = lambda chat_id=None: 0
            self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: {"blockers": []}
            candidate = {
                "ticker": "BTCUSDT",
                "interval": "15m",
                "direction": "long",
                "data": {"risk_levels": {"rr_ratio": 1.67}, "risk_blockers": []},
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 88,
                    "setup_score": 88,
                    "rr_now": 1.67,
                },
            }
            self.assertIsNone(self.bot._testnet_candidate_block_reason_v735(987654321, candidate))
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_count
            self.bot._build_testnet_trade_plan_v734 = old_plan

    def test_demo_analytics_store_details_not_user_card(self) -> None:
        row = {
            "ticker": "BTCUSDT",
            "tf": "15m",
            "status": "ENTER_NOW",
            "entry_now": 88,
            "setup": 88,
            "rr": 1.67,
            "testnet_gate": "подробная техническая причина для локального анализа",
        }
        visible = "\n".join(self.bot._format_scan_rows([row]))
        self.assertIn("Entry: 88/100", visible)
        self.assertNotIn("подробная техническая причина", visible)

        old_file = self.bot.DEMO_ANALYTICS_STATE_FILE
        with tempfile.TemporaryDirectory() as tmp:
            self.bot.DEMO_ANALYTICS_STATE_FILE = os.path.join(tmp, "demo_analysis_state.json")
            try:
                self.bot._demo_analysis_record_cycle_v736(
                    987654321,
                    [row],
                    decision={"opened": False, "status": "NO_TRADE", "reason": "коротко для пользователя"},
                )
                state = self.bot._demo_analysis_load_v736()
                stored = state["cycles"][-1]
                self.assertEqual(stored["user_visible"]["reason"], "коротко для пользователя")
                self.assertIn("подробная техническая причина", stored["scan"]["top"][0]["testnet_gate"])
            finally:
                self.bot.DEMO_ANALYTICS_STATE_FILE = old_file

    def test_public_pnl_waits_for_bot_closed_trades(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_income = self.bot._testnet_income_stats_v734
        old_monitor = self.bot._recent_testnet_monitor_events_v730
        old_connection = self.bot._testnet_connection_status_v740
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_income_stats_v734 = lambda: {
                "ok": True,
                "closed": 2,
                "wins": 1,
                "losses": 1,
                "winrate": 50.0,
                "net": 12.34,
            }
            self.bot._recent_testnet_monitor_events_v730 = lambda chat_id=None, limit=6: []
            self.bot._testnet_connection_status_v740 = lambda force=False: {
                "state": "READY_TO_TRADE",
                "signed_ok": True,
                "reason": "ok",
            }
            text = self.bot.format_autobot_menu(987654321)
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_income_stats_v734 = old_income
            self.bot._recent_testnet_monitor_events_v730 = old_monitor
            self.bot._testnet_connection_status_v740 = old_connection

        self.assertIn("Закрытые сделки бота: <b>0</b>", text)
        self.assertIn("Winrate / PnL: <b>н/д</b>", text)
        self.assertNotIn("+12.340 USDT", text)

    def test_connection_line_is_explicit(self) -> None:
        old_status = self.bot._testnet_connection_status_v740
        try:
            self.bot._testnet_connection_status_v740 = lambda force=False: {
                "state": "READY_TO_TRADE",
                "signed_ok": True,
                "reason": "signed API OK, real Testnet submit ON",
            }
            self.assertIn("Binance: 🟢 <b>READY</b>", self.bot._testnet_connection_line_v740())
        finally:
            self.bot._testnet_connection_status_v740 = old_status

    def test_public_pnl_uses_attributed_bot_rows(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_income = self.bot._testnet_income_stats_v734
        old_closed = self.bot._testnet_closed_trade_rows_v742
        old_connection = self.bot._testnet_connection_status_v740
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_income_stats_v734 = lambda: {"ok": True, "closed": 8, "net": 999.0, "winrate": 100.0}
            self.bot._testnet_closed_trade_rows_v742 = lambda chat_id=None, limit=200: [
                {"pnl": {"status": "ATTRIBUTED", "realized_usdt": 2.5}},
                {"pnl": {"status": "ATTRIBUTED", "realized_usdt": -1.0}},
            ]
            self.bot._testnet_connection_status_v740 = lambda force=False: {
                "state": "READY_TO_TRADE",
                "signed_ok": True,
                "reason": "ok",
            }
            text = self.bot.format_autobot_menu(987654321)
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_income_stats_v734 = old_income
            self.bot._testnet_closed_trade_rows_v742 = old_closed
            self.bot._testnet_connection_status_v740 = old_connection

        self.assertIn("Winrate: <b>50.0%</b>", text)
        self.assertIn("+1.500 USDT", text)
        self.assertNotIn("+999.000 USDT", text)


if __name__ == "__main__":
    unittest.main()
