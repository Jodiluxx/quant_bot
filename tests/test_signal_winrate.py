from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quant_bot.signal_winrate import (
    outcome_hint,
    outcome_legend_lines,
    result_suffix,
    signal_status_icon,
    signed_percent_text,
    winrate_text,
)


class SignalWinrateHelperTests(unittest.TestCase):
    def test_winrate_and_signed_percent_text_are_stable(self) -> None:
        self.assertEqual(winrate_text(66.666), "66.7%")
        self.assertEqual(winrate_text(None), "н/д")
        self.assertEqual(winrate_text("bad"), "н/д")
        self.assertEqual(signed_percent_text(1.234), "+1.23%")
        self.assertEqual(signed_percent_text(-0.5), "-0.50%")
        self.assertEqual(signed_percent_text(None), "н/д")

    def test_status_icon_and_result_suffix(self) -> None:
        due = datetime(2026, 6, 7, 12, 30, tzinfo=timezone.utc)

        self.assertEqual(signal_status_icon("WIN"), "🟢")
        self.assertEqual(signal_status_icon("loss"), "🔴")
        self.assertEqual(signal_status_icon("PENDING"), "⏳")
        self.assertEqual(signal_status_icon("other"), "⚪")
        self.assertEqual(result_suffix("WIN", 0.25), " +0.25%")
        self.assertEqual(result_suffix("LOSS", -1.0), " -1.00%")
        self.assertEqual(result_suffix("PENDING", due_at=due), " проверка 12:30 UTC")
        self.assertEqual(result_suffix("WIN", "bad"), "")

    def test_outcome_explanations_are_human_readable(self) -> None:
        self.assertEqual(outcome_hint("WIN"), "в сторону сигнала")
        self.assertEqual(outcome_hint("loss"), "против сигнала")
        self.assertEqual(outcome_hint("FLAT"), "нейтрально: слабое движение")
        self.assertEqual(outcome_hint("PENDING"), "ждём закрытия TF")

        legend = "\n".join(outcome_legend_lines())
        self.assertIn("FLAT", legend)
        self.assertIn("не победа и не поражение", legend)


if __name__ == "__main__":
    unittest.main()
