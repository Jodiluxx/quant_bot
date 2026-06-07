from __future__ import annotations

import unittest

from quant_bot.code_audit import audit_payload, cleanup_priority
from quant_bot.migration import checklist_payload, migration_summary


class MigrationChecklistTests(unittest.TestCase):
    def test_migration_summary_has_pending_work(self) -> None:
        summary = migration_summary()
        self.assertGreater(summary["total"], 0)
        self.assertGreaterEqual(summary["done"], 1)
        self.assertGreaterEqual(summary["pending"], 1)
        self.assertGreater(summary["progress"], 0)

    def test_payload_tracks_runtime_counts(self) -> None:
        payload = checklist_payload("v-test", [("base", "x")], {"fn": object()})
        self.assertEqual(payload["runtime_version"], "v-test")
        self.assertEqual(payload["runtime_layers"], 1)
        self.assertEqual(payload["active_functions"], 1)
        self.assertTrue(payload["next_steps"])
        self.assertIn("code_audit", payload)
        self.assertTrue(payload["cleanup_priority"])

    def test_code_audit_tracks_duplicate_legacy_definitions(self) -> None:
        payload = audit_payload(active_runtime_names={"format_signal_summary", "async_handle_update"})
        duplicates = {row["name"]: row for row in payload["top_duplicates"]}

        self.assertGreater(payload["total_definitions"], 1000)
        self.assertIn("async_handle_update", duplicates)
        self.assertGreaterEqual(duplicates["async_handle_update"]["lines"][-1], duplicates["async_handle_update"]["lines"][0])
        self.assertGreater(payload["duplicate_names"], 100)
        self.assertIn("format_signal_summary", payload["active_runtime_lines"])
        self.assertTrue(cleanup_priority(payload))


if __name__ == "__main__":
    unittest.main()
