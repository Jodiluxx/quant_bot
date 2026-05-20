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

    def test_auto_safety_does_nothing_when_position_is_protected(self) -> None:
        plan = {"plan_id": "safe-1", "chat_id": "1", "ticker": "BTCUSDT", "api_symbol": "BTCUSDT"}
        monitor = {"status": "PROTECTED", "ok": True, "has_position": True}
        result = self.bot._testnet_auto_safety_after_monitor_v741("1", plan, monitor)
        self.assertFalse(result["triggered"])
        self.assertEqual(result["actions"], {})

    def test_auto_safety_pauses_cancels_and_closes_unprotected_position(self) -> None:
        plan = {
            "plan_id": "risk-1",
            "chat_id": "1",
            "ticker": "BTCUSDT",
            "api_symbol": "BTCUSDT",
            "interval": "15m",
            "direction": "long",
            "blockers": [],
            "entry_order": {"quantity_est": 0.001, "entry_reference": 100.0, "leverage": 5},
        }
        monitor = {
            "status": "UNPROTECTED",
            "ok": False,
            "has_position": True,
            "position_amt": 0.001,
            "mark_price": 100.0,
            "reason": "missing reduceOnly STOP_MARKET SL",
        }
        calls = []
        old_recent = self.bot._testnet_recent_auto_safety_v741
        old_pause = self.bot.set_safety_pause
        old_cancel = self.bot.cancel_testnet_open_orders_v741
        old_cancel_algo = self.bot.cancel_testnet_algo_orders_v741
        old_close = self.bot.submit_testnet_emergency_close_position_v741
        old_record = self.bot._record_testnet_auto_safety_v741
        old_real_record = self.bot._record_testnet_real_order_result_v729
        self.bot._testnet_recent_auto_safety_v741 = lambda plan_id, status, minutes=30: None
        self.bot.set_safety_pause = lambda chat_id, minutes=None, reason=None: calls.append(("pause", chat_id, minutes, reason)) or True
        self.bot.cancel_testnet_open_orders_v741 = lambda symbol, reason="": {"ok": True, "symbol": symbol, "reason": reason}
        self.bot.cancel_testnet_algo_orders_v741 = lambda symbol, reason="": {"ok": True, "symbol": symbol, "reason": reason}
        self.bot.submit_testnet_emergency_close_position_v741 = lambda plan, monitor=None, reason="": {"ok": True, "reason": reason}
        self.bot._record_testnet_auto_safety_v741 = lambda chat_id, plan, payload: dict(payload, recorded=True)
        self.bot._record_testnet_real_order_result_v729 = lambda kind, plan, result: result
        try:
            result = self.bot._testnet_auto_safety_after_monitor_v741("1", plan, monitor)
        finally:
            self.bot._testnet_recent_auto_safety_v741 = old_recent
            self.bot.set_safety_pause = old_pause
            self.bot.cancel_testnet_open_orders_v741 = old_cancel
            self.bot.cancel_testnet_algo_orders_v741 = old_cancel_algo
            self.bot.submit_testnet_emergency_close_position_v741 = old_close
            self.bot._record_testnet_auto_safety_v741 = old_record
            self.bot._record_testnet_real_order_result_v729 = old_real_record

        self.assertTrue(result["triggered"])
        self.assertEqual(calls[0][0], "pause")
        self.assertEqual(calls[0][2], self.bot.TESTNET_AUTO_SAFETY_PAUSE_MIN)
        self.assertIn("cancel_open_orders", result["actions"])
        self.assertIn("cancel_algo_orders", result["actions"])
        self.assertIn("emergency_close_position", result["actions"])

    def test_cancel_helpers_use_signed_delete_endpoints(self) -> None:
        calls = []
        old_guard = self.bot._testnet_mutation_guard_v741
        old_delete = self.bot._testnet_delete_signed_v741
        self.bot._testnet_mutation_guard_v741 = lambda: []
        self.bot._testnet_delete_signed_v741 = lambda path, params=None: calls.append((path, params)) or {"ok": True, "status_code": 200, "payload": {"code": 200}}
        try:
            regular = self.bot.cancel_testnet_open_orders_v741("BTCUSDT")
            algo = self.bot.cancel_testnet_algo_orders_v741("BTCUSDT")
        finally:
            self.bot._testnet_mutation_guard_v741 = old_guard
            self.bot._testnet_delete_signed_v741 = old_delete

        self.assertTrue(regular["ok"])
        self.assertTrue(algo["ok"])
        self.assertEqual(calls[0][0], self.bot.TESTNET_CANCEL_ALL_OPEN_ORDERS_PATH)
        self.assertEqual(calls[1][0], self.bot.TESTNET_CANCEL_ALL_ALGO_OPEN_ORDERS_PATH)
        self.assertEqual(calls[0][1]["symbol"], "BTCUSDT")

    def test_lifecycle_attributes_closed_trade_pnl_by_symbol_and_time(self) -> None:
        plan = {
            "plan_id": "pnl-1",
            "created_at": "2026-05-20T10:00:00+00:00",
            "mode": "testnet",
            "ticker": "BTCUSDT",
            "api_symbol": "BTCUSDT",
            "interval": "15m",
            "direction": "long",
            "strategy": "test",
        }
        events = [
            {
                "type": self.bot.TESTNET_REAL_EVENTS_FILE_KIND,
                "kind": "real_entry",
                "plan_id": "pnl-1",
                "ok": True,
                "submitted": True,
                "ts": "2026-05-20T10:00:10+00:00",
                "response": {"orderId": 10},
            },
            {
                "type": self.bot.TESTNET_MONITOR_EVENTS_FILE_KIND,
                "plan_id": "pnl-1",
                "ok": True,
                "status": "NO_POSITION",
                "ts": "2026-05-20T10:30:00+00:00",
                "evaluation": {"status": "NO_POSITION"},
            },
        ]
        income_time = int(self.bot._safety_parse_dt_v716("2026-05-20T10:29:30+00:00").timestamp() * 1000)
        old_load = self.bot._execution_load_state_v715
        old_income = self.bot._testnet_income_stats_v734
        self.bot._execution_load_state_v715 = lambda: {"plans": [plan], "events": events}
        self.bot._testnet_income_stats_v734 = lambda: {
            "ok": True,
            "rows": [
                {"symbol": "BTCUSDT", "income": "1.25", "time": income_time},
                {"symbol": "ETHUSDT", "income": "100", "time": income_time},
            ],
        }
        try:
            row = self.bot._testnet_lifecycle_row_v740(plan)
        finally:
            self.bot._execution_load_state_v715 = old_load
            self.bot._testnet_income_stats_v734 = old_income

        self.assertEqual(row["status"], "CLOSED_WIN")
        self.assertEqual(row["pnl"]["status"], "ATTRIBUTED")
        self.assertAlmostEqual(row["pnl"]["realized_usdt"], 1.25)


if __name__ == "__main__":
    unittest.main()
