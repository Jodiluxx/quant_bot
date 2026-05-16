from __future__ import annotations

import unittest

from quant_bot.execution_gateway import (
    event_status,
    execution_plan_view,
    protection_status,
    reconcile_testnet_plan,
)


class ExecutionGatewayTests(unittest.TestCase):
    def test_reconciles_accepted_entry_and_protection(self) -> None:
        plan = {
            "plan_id": "p1",
            "ticker": "BTCUSDT",
            "interval": "15m",
            "direction": "long",
            "entry_order": {"side": "BUY", "quantity_est": 0.01, "notional_est": 100},
        }
        rec = reconcile_testnet_plan(plan, [
            {"kind": "entry", "ok": True, "ts": "2026-05-16T00:00:00+00:00"},
            {"kind": "protection", "orders": [{"ok": True}, {"ok": True}], "ts": "2026-05-16T00:00:01+00:00"},
        ])
        self.assertEqual(rec["overall"], "ACCEPTED")
        self.assertEqual(rec["entry_status"], "ACCEPTED")
        self.assertEqual(rec["protection_status"], "ACCEPTED")

    def test_event_statuses_are_explicit(self) -> None:
        self.assertEqual(event_status({"ok": True}), "ACCEPTED")
        self.assertEqual(event_status({"submitted": False}), "SKIPPED")
        self.assertEqual(event_status({"ok": False, "submitted": True}), "REJECTED")
        self.assertEqual(event_status(None), "MISSING")
        self.assertEqual(protection_status({"orders": [{"ok": True}, {"ok": False, "submitted": True}]}), "REJECTED")

    def test_execution_plan_view_formats_quantity(self) -> None:
        view = execution_plan_view({"entry_order": {"quantity_est": 0.123456789, "notional_est": "25.5"}})
        self.assertEqual(view["quantity_text"], "0.123457")
        self.assertEqual(view["notional"], 25.5)


if __name__ == "__main__":
    unittest.main()
