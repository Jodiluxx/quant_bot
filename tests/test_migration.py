from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
