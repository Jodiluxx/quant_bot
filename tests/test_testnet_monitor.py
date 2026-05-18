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


if __name__ == "__main__":
    unittest.main()
