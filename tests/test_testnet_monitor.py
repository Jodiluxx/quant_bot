from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from quant_bot.legacy import load_bot_module


class TestnetPositionMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def test_monitor_skips_outside_testnet_mode(self) -> None:
        with patch.dict(os.environ, {"BOT_EXECUTION_MODE": "paper"}, clear=False):
            result = self.bot.run_testnet_position_monitor(chat_id="1")
        self.assertFalse(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertIn("BOT_EXECUTION_MODE", result["reason"])

    def test_execution_keyboard_exposes_monitor_callback(self) -> None:
        keyboard = self.bot.execution_status_keyboard_v715()
        callbacks = [
            button.get("callback_data")
            for row in keyboard.get("inline_keyboard", [])
            for button in row
        ]
        self.assertIn("testnet_monitor", callbacks)

    def test_snapshot_fetches_algo_open_orders_for_protection(self) -> None:
        calls = []

        def fake_get(path, params=None):
            calls.append(path)
            if path == self.bot.TESTNET_POSITION_RISK_PATH:
                return {"ok": True, "payload": [{"symbol": "BNBUSDT", "positionAmt": "-0.02"}]}
            if path == self.bot.TESTNET_OPEN_ORDERS_PATH:
                return {"ok": True, "payload": []}
            if path == self.bot.TESTNET_OPEN_ALGO_ORDERS_PATH:
                return {"ok": True, "payload": [{"symbol": "BNBUSDT", "orderType": "STOP_MARKET"}]}
            return {"ok": False, "reason": path}

        old_get = self.bot._testnet_get_signed_v730
        old_guard = self.bot._testnet_monitor_read_guard_v730
        self.bot._testnet_get_signed_v730 = fake_get
        self.bot._testnet_monitor_read_guard_v730 = lambda: []
        try:
            snapshot = self.bot.fetch_testnet_position_snapshot({"ticker": "BNBUSDT", "api_symbol": "BNBUSDT"})
        finally:
            self.bot._testnet_get_signed_v730 = old_get
            self.bot._testnet_monitor_read_guard_v730 = old_guard

        self.assertTrue(snapshot["ok"])
        self.assertIn(self.bot.TESTNET_OPEN_ALGO_ORDERS_PATH, calls)
        self.assertEqual(len(snapshot["orders_response"]), 1)

    def test_lifecycle_row_links_entry_protection_and_monitor(self) -> None:
        plan = {
            "plan_id": "life-1",
            "created_at": "2026-05-20T00:00:00+00:00",
            "mode": "testnet",
            "ticker": "BTCUSDT",
            "api_symbol": "BTCUSDT",
            "interval": "15m",
            "direction": "long",
            "strategy": "test",
        }
        events = [
            {"type": self.bot.TESTNET_REAL_EVENTS_FILE_KIND, "kind": "real_entry", "plan_id": "life-1", "ok": True, "submitted": True, "response": {"orderId": 123}},
            {"type": self.bot.TESTNET_REAL_EVENTS_FILE_KIND, "kind": "real_protection", "plan_id": "life-1", "ok": True, "submitted": True, "orders": [{"ok": True}]},
            {"type": self.bot.TESTNET_MONITOR_EVENTS_FILE_KIND, "plan_id": "life-1", "ok": True, "status": "PROTECTED", "evaluation": {"status": "PROTECTED"}},
        ]
        old_load = self.bot._execution_load_state_v715
        self.bot._execution_load_state_v715 = lambda: {"plans": [plan], "events": events}
        try:
            row = self.bot._testnet_lifecycle_row_v740(plan)
        finally:
            self.bot._execution_load_state_v715 = old_load

        self.assertEqual(row["status"], "PROTECTED")
        self.assertEqual(row["entry"]["order_id"], 123)
        self.assertTrue(row["protection"]["ok"])


if __name__ == "__main__":
    unittest.main()
