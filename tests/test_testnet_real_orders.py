from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from quant_bot.legacy import load_bot_module


class RealTestnetOrderGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def _plan(self) -> dict:
        return {
            "plan_id": "p1",
            "chat_id": "1",
            "mode": "testnet",
            "ticker": "BTCUSDT",
            "api_symbol": "BTCUSDT",
            "interval": "15m",
            "direction": "long",
            "blockers": [],
            "entry_order": {
                "side": "BUY",
                "type": "MARKET",
                "quantity_est": 0.001,
                "entry_reference": 100.0,
                "client_order_id": "p1",
                "leverage": 5,
            },
            "protection_orders": [
                {"side": "SELL", "type": "STOP_MARKET", "stop_price": 95.0, "reduce_only": True, "label": "SL"},
                {"side": "SELL", "type": "TAKE_PROFIT_MARKET", "stop_price": 110.0, "reduce_only": True, "label": "TP1"},
                {"side": "SELL", "type": "TAKE_PROFIT_MARKET", "stop_price": 120.0, "reduce_only": True, "label": "TP2"},
            ],
        }

    def test_real_entry_is_blocked_without_explicit_real_flag(self) -> None:
        env = {
            "BOT_EXECUTION_MODE": "testnet",
            "BINANCE_TESTNET_ORDER_SUBMIT": "1",
            "BINANCE_FUTURES_TESTNET_API_KEY": "key",
            "BINANCE_FUTURES_TESTNET_API_SECRET": "secret",
        }
        with patch.dict(os.environ, env, clear=False):
            result = self.bot.submit_testnet_real_entry_order(
                self._plan(),
                {"entry_test_ok": True, "protection_test_ok": True},
            )
        self.assertFalse(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertIn("BINANCE_TESTNET_REAL_ORDER_SUBMIT", result["reason"])

    def test_real_entry_is_blocked_when_validation_failed(self) -> None:
        env = {
            "BOT_EXECUTION_MODE": "testnet",
            "BINANCE_TESTNET_ORDER_SUBMIT": "1",
            "BINANCE_TESTNET_REAL_ORDER_SUBMIT": "1",
            "BINANCE_FUTURES_TESTNET_API_KEY": "key",
            "BINANCE_FUTURES_TESTNET_API_SECRET": "secret",
        }
        with patch.dict(os.environ, env, clear=False):
            result = self.bot.submit_testnet_real_entry_order(
                self._plan(),
                {"entry_test_ok": False, "protection_test_ok": True},
            )
        self.assertFalse(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertIn("entry /order/test", result["reason"])

    def test_real_protection_order_builder_uses_real_endpoint_shape(self) -> None:
        params, geometry = self.bot._real_protection_order_params_v729(self._plan())
        self.assertTrue(geometry["ok"])
        self.assertEqual([label for label, _ in params], ["SL", "TP1", "TP2"])
        self.assertEqual(params[0][1]["reduceOnly"], "true")
        self.assertEqual(params[1][1]["type"], "TAKE_PROFIT_MARKET")


if __name__ == "__main__":
    unittest.main()
