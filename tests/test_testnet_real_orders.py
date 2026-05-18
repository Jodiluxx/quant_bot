from __future__ import annotations

import os
from decimal import Decimal
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
            "BINANCE_TESTNET_REAL_ORDER_SUBMIT": "0",
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

    def test_precision_normalizes_bnb_entry_and_unsplittable_tp(self) -> None:
        plan = self._plan()
        plan.update({"ticker": "BNBUSDT", "api_symbol": "BNBUSDT", "direction": "short"})
        plan["entry_order"].update({
            "side": "SELL",
            "quantity_est": 0.00732933,
            "entry_reference": 648.080664,
        })
        plan["protection_orders"] = [
            {"side": "BUY", "type": "STOP_MARKET", "stop_price": 653.34535714, "reduce_only": True, "label": "SL"},
            {"side": "BUY", "type": "TAKE_PROFIT_MARKET", "stop_price": 639.65107143, "reduce_only": True, "label": "TP1"},
            {"side": "BUY", "type": "TAKE_PROFIT_MARKET", "stop_price": 634.51571429, "reduce_only": True, "label": "TP2"},
        ]
        symbols = {
            "BNBUSDT": {
                "filters_map": {
                    "MARKET_LOT_SIZE": {"stepSize": "0.01", "minQty": "0.01", "maxQty": "100000"},
                    "LOT_SIZE": {"stepSize": "0.01", "minQty": "0.01", "maxQty": "100000"},
                    "PRICE_FILTER": {"tickSize": "0.010"},
                    "MIN_NOTIONAL": {"notional": "5"},
                }
            }
        }
        old_symbols = self.bot._testnet_exchange_symbols_v734
        self.bot._testnet_exchange_symbols_v734 = lambda force=False: symbols
        try:
            entry = self.bot._entry_order_test_params_v719(plan)
            protection, geometry = self.bot.build_testnet_protection_order_tests(plan)
        finally:
            self.bot._testnet_exchange_symbols_v734 = old_symbols

        self.assertEqual(entry["quantity"], "0.01")
        self.assertEqual([row["label"] for row in protection], ["SL", "TP1"])
        self.assertTrue(geometry["ok"])
        for row in protection:
            self.assertEqual(Decimal(row["quantity"]) % Decimal("0.01"), Decimal("0.00"))
            self.assertEqual(Decimal(row["triggerPrice"]) % Decimal("0.01"), Decimal("0.00"))
        self.assertEqual(protection[0]["triggerPrice"], "653.35")
        self.assertEqual(protection[1]["quantity"], "0.01")


if __name__ == "__main__":
    unittest.main()
