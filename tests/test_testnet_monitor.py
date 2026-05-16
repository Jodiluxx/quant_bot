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


if __name__ == "__main__":
    unittest.main()
