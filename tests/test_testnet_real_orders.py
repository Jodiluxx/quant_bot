from __future__ import annotations

import os
import tempfile
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

    def test_signed_payload_uses_testnet_server_time_offset(self) -> None:
        old_local_time = self.bot._testnet_local_time_ms_v758
        old_sync = self.bot._testnet_sync_server_time_v758
        try:
            self.bot._testnet_local_time_ms_v758 = lambda: 2_000_000
            self.bot._testnet_sync_server_time_v758 = lambda force=False: {"offset_ms": -1500, "error": None}
            signed, _ = self.bot._testnet_signed_payload_v719({"symbol": "BTCUSDT"}, "secret")
        finally:
            self.bot._testnet_local_time_ms_v758 = old_local_time
            self.bot._testnet_sync_server_time_v758 = old_sync

        expected = 2_000_000 - 1500 - self.bot.TESTNET_TIME_SYNC_SAFETY_MS
        self.assertEqual(signed["timestamp"], str(expected))

    def test_signed_post_retries_timestamp_error_after_forced_time_sync(self) -> None:
        class FakeResponse:
            def __init__(self, status_code: int, payload: dict):
                self.status_code = status_code
                self._payload = payload
                self.text = "{}"
                self.headers = {}

            def json(self) -> dict:
                return self._payload

        class FakeSession:
            def __init__(self) -> None:
                self.requests = []

            def post(self, url, data=None, headers=None, timeout=None):
                self.requests.append(dict(data or {}))
                if len(self.requests) == 1:
                    return FakeResponse(400, {"code": -1021, "msg": "Timestamp for this request was ahead"})
                return FakeResponse(200, {"orderId": 123})

        env = {
            "BINANCE_FUTURES_TESTNET_API_KEY": "key",
            "BINANCE_FUTURES_TESTNET_API_SECRET": "secret",
        }
        fake_session = FakeSession()
        force_calls = []
        old_session = self.bot._session
        old_timestamp = self.bot._testnet_timestamp_ms_v758
        try:
            self.bot._session = fake_session

            def fake_timestamp(force_sync=False):
                force_calls.append(force_sync)
                return 2_000 if force_sync else 1_000

            self.bot._testnet_timestamp_ms_v758 = fake_timestamp
            with patch.dict(os.environ, env, clear=False):
                result = self.bot._testnet_post_signed_v719("/fapi/v1/order/test", {"symbol": "BTCUSDT"})
        finally:
            self.bot._session = old_session
            self.bot._testnet_timestamp_ms_v758 = old_timestamp

        self.assertTrue(result["ok"])
        self.assertTrue(result["retried_after_time_sync"])
        self.assertEqual(force_calls, [False, True])
        self.assertEqual([row["timestamp"] for row in fake_session.requests], ["1000", "2000"])

    def test_real_protection_order_builder_uses_real_endpoint_shape(self) -> None:
        params, geometry = self.bot._real_protection_order_params_v729(self._plan())
        self.assertTrue(geometry["ok"])
        self.assertEqual([label for label, _ in params], ["SL", "TP1", "TP2"])
        client_ids = [row["clientAlgoId"] for _, row in params]
        self.assertEqual(len(client_ids), len(set(client_ids)))
        self.assertTrue(all(len(x) <= 36 for x in client_ids))
        self.assertTrue(client_ids[0].startswith("rp_SL_"))
        self.assertTrue(client_ids[1].startswith("rp_TP1_"))
        self.assertTrue(client_ids[2].startswith("rp_TP2_"))
        self.assertEqual(params[0][1]["algoType"], "CONDITIONAL")
        self.assertEqual(params[0][1]["positionSide"], "BOTH")
        self.assertEqual(params[0][1]["reduceOnly"], "true")
        self.assertEqual(params[0][1]["newOrderRespType"], "ACK")
        self.assertEqual(params[1][1]["type"], "TAKE_PROFIT_MARKET")

    def test_protection_preflight_detects_immediate_trigger_before_real_entry(self) -> None:
        plan = self._plan()
        old_price = self.bot.get_price
        old_rules = self.bot._testnet_rules_summary_v739
        try:
            self.bot.get_price = lambda ticker: 94.0
            self.bot._testnet_rules_summary_v739 = lambda symbol: {"tick": "0.1"}
            reason = self.bot._testnet_protection_immediate_trigger_reason_v773(plan)
        finally:
            self.bot.get_price = old_price
            self.bot._testnet_rules_summary_v739 = old_rules

        self.assertIn("immediately trigger", reason)
        self.assertIn("SL", reason)

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

    def test_submit_testnet_trade_runs_real_entry_after_validation(self) -> None:
        plan = self._plan()
        calls = []

        old_build = self.bot._build_testnet_trade_plan_v734
        old_entry_test = self.bot.submit_testnet_order_test
        old_protection_test = self.bot.submit_testnet_protection_order_tests
        old_leverage = self.bot.submit_testnet_set_leverage
        old_real_entry = self.bot.submit_testnet_real_entry_order
        old_real_protection = self.bot.submit_testnet_real_protection_orders
        old_monitor = self.bot._testnet_monitor_for_plan_v737
        old_record = self.bot._record_testnet_trade_attempt_v734
        old_price = self.bot.get_price

        try:
            self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: plan
            self.bot.submit_testnet_order_test = lambda p: calls.append("entry_test") or {"ok": True, "submitted": True}
            self.bot.submit_testnet_protection_order_tests = lambda p: calls.append("protection_test") or {"ok": True, "orders": [{"ok": True}]}
            self.bot.submit_testnet_set_leverage = lambda p: calls.append("leverage") or {"ok": True}
            self.bot.submit_testnet_real_entry_order = lambda p, validation: calls.append("real_entry") or {"ok": True, "submitted": True, "response": {"orderId": 1}}
            self.bot.submit_testnet_real_protection_orders = lambda p, entry: calls.append("real_protection") or {"ok": True, "orders": [{"ok": True}]}
            self.bot._testnet_monitor_for_plan_v737 = lambda p, delay_sec=0.2: {"status": "PROTECTED"}
            self.bot._record_testnet_trade_attempt_v734 = lambda *args, **kwargs: calls.append("record")
            self.bot.get_price = lambda ticker: 100.0

            result = self.bot._submit_testnet_trade_v734("1", {"ticker": "BTCUSDT"})
        finally:
            self.bot._build_testnet_trade_plan_v734 = old_build
            self.bot.submit_testnet_order_test = old_entry_test
            self.bot.submit_testnet_protection_order_tests = old_protection_test
            self.bot.submit_testnet_set_leverage = old_leverage
            self.bot.submit_testnet_real_entry_order = old_real_entry
            self.bot.submit_testnet_real_protection_orders = old_real_protection
            self.bot._testnet_monitor_for_plan_v737 = old_monitor
            self.bot._record_testnet_trade_attempt_v734 = old_record
            self.bot.get_price = old_price

        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], "done")
        self.assertEqual(
            calls,
            ["entry_test", "protection_test", "leverage", "real_entry", "real_protection", "record"],
        )

    def test_submit_testnet_trade_reports_protection_validation_exception(self) -> None:
        plan = self._plan()
        calls = []

        old_build = self.bot._build_testnet_trade_plan_v734
        old_entry_test = self.bot.submit_testnet_order_test
        old_protection_test = self.bot.submit_testnet_protection_order_tests
        old_record = self.bot._record_testnet_trade_attempt_v734

        try:
            self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: plan
            self.bot.submit_testnet_order_test = lambda p: {"ok": True, "submitted": True}

            def broken_protection(_plan):
                raise RuntimeError("boom")

            self.bot.submit_testnet_protection_order_tests = broken_protection
            self.bot._record_testnet_trade_attempt_v734 = lambda *args, **kwargs: calls.append(args)

            result = self.bot._submit_testnet_trade_v734("1", {"ticker": "BTCUSDT"})
        finally:
            self.bot._build_testnet_trade_plan_v734 = old_build
            self.bot.submit_testnet_order_test = old_entry_test
            self.bot.submit_testnet_protection_order_tests = old_protection_test
            self.bot._record_testnet_trade_attempt_v734 = old_record

        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "validation")
        self.assertIn("protection_test exception", result["reason"])
        self.assertEqual(len(calls), 1)

    def test_testnet_journal_compatibility_helper_deduplicates_existing_event(self) -> None:
        plan = self._plan()
        result = {
            "ts": "2026-06-03T10:00:00+00:00",
            "submitted": True,
            "ok": True,
            "status_code": 200,
            "request": {"symbol": "BTCUSDT"},
            "response": {},
        }
        old_file = self.bot.TESTNET_JOURNAL_FILE
        with tempfile.TemporaryDirectory() as tmp:
            journal_path = os.path.join(tmp, "testnet_journal.json")
            self.bot.TESTNET_JOURNAL_FILE = journal_path
            try:
                first = self.bot._testnet_journal_record_v721("entry", plan, result)
                second = self.bot._record_testnet_journal_event_v721("entry", plan, result)
                state = self.bot._testnet_journal_load_v721()
            finally:
                self.bot.TESTNET_JOURNAL_FILE = old_file

        self.assertEqual(first, second)
        self.assertEqual(len(state.get("events") or []), 1)
        self.assertTrue(callable(self.bot._record_testnet_journal_event_v721))

    def test_testnet_exploration_adds_strong_wait_retest_candidate(self) -> None:
        data = {
            "direction": "long",
            "confidence": 76,
            "risk_blockers": [],
            "risk_warnings": ["minor warning"],
            "risk_levels": {"rr_ratio": 1.67},
            "entry_plan": {
                "status": "WAIT_RETEST",
                "entry_now_score": 69,
                "setup_score": 76,
                "rr_now": 1.67,
                "sl": 95.0,
                "tp1": 110.0,
                "tp2": 120.0,
            },
        }

        rows = self.bot._paper_strategy_candidates("1", "BTCUSDT", "15m", data)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["strategy"], "retest_explore_v1")
        self.assertTrue(rows[0]["testnet_exploration"])
        self.assertEqual(rows[0]["direction"], "long")

    def test_testnet_exploration_does_not_add_weak_wait_candidate(self) -> None:
        data = {
            "direction": "short",
            "confidence": 80,
            "risk_blockers": [],
            "risk_levels": {"rr_ratio": 1.67},
            "entry_plan": {
                "status": "WAIT_RETEST",
                "entry_now_score": 40,
                "setup_score": 80,
                "rr_now": 1.67,
            },
        }

        rows = self.bot._paper_strategy_candidates("1", "BTCUSDT", "15m", data)

        self.assertEqual(rows, [])
        self.assertIn("EntryNow", self.bot._testnet_exploration_data_block_v763(data))

    def test_testnet_exploration_candidate_can_pass_testnet_gate(self) -> None:
        data = {
            "direction": "long",
            "confidence": 76,
            "risk_blockers": [],
            "risk_warnings": [],
            "risk_levels": {"rr_ratio": 1.67},
            "entry_plan": {
                "status": "WAIT_RETEST",
                "entry_now_score": 70,
                "setup_score": 76,
                "rr_now": 1.67,
                "live_price": 100.0,
                "sl": 95.0,
                "tp1": 110.0,
                "tp2": 120.0,
            },
        }
        candidate = self.bot._paper_strategy_candidates("1", "BTCUSDT", "15m", data)[0]
        old_plan = self.bot._build_testnet_trade_plan_v734
        old_quality = self.bot._adaptive_quality_attach_v745
        try:
            self.bot._build_testnet_trade_plan_v734 = lambda chat_id, cand: {"blockers": []}
            self.bot._adaptive_quality_attach_v745 = lambda chat_id, cand: {"penalty": 0}

            reason = self.bot._testnet_candidate_block_reason_v735(
                "1",
                candidate,
                active_positions=[],
                pos_err=None,
                today_count=0,
            )
        finally:
            self.bot._build_testnet_trade_plan_v734 = old_plan
            self.bot._adaptive_quality_attach_v745 = old_quality

        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
