from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quant_bot.signal_winrate import (
    action_note_text,
    basis_counts_text,
    outcome_hint,
    outcome_legend_lines,
    outcome_streak_text,
    pending_check_text,
    recent_outcome_sequence,
    result_suffix,
    sample_quality_badge,
    sample_quality_text,
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

    def test_sample_quality_text_explains_small_and_large_samples(self) -> None:
        self.assertIn("данных нет", sample_quality_text(0))
        self.assertIn("очень мало данных", sample_quality_text(5))
        self.assertIn("нужно ещё 12", sample_quality_text(18))
        self.assertIn("выборка рабочая", sample_quality_text(30))
        self.assertIn("выборка сильная", sample_quality_text(120))

    def test_sample_quality_badge_is_compact_for_menu_cards(self) -> None:
        self.assertEqual(sample_quality_badge(0), "нет данных")
        self.assertEqual(sample_quality_badge(5), "очень мало")
        self.assertEqual(sample_quality_badge(18), "мало")
        self.assertEqual(sample_quality_badge(30), "рабочая")
        self.assertEqual(sample_quality_badge(120), "сильная")

    def test_basis_counts_text_separates_wr_base_from_flat(self) -> None:
        self.assertEqual(
            basis_counts_text(2, 1, 3, 4),
            "WR база: 3 WIN/LOSS | FLAT отдельно: 3 | ждут: 4",
        )
        self.assertEqual(
            basis_counts_text("bad", None, -5),
            "WR база: 0 WIN/LOSS | FLAT отдельно: 0",
        )

    def test_recent_outcome_sequence_and_streak_are_compact(self) -> None:
        rows = [
            {"status": "LOSS"},
            {"status": "LOSS"},
            {"status": "FLAT"},
            {"status": "WIN"},
            {"status": "PENDING"},
        ]

        self.assertEqual(recent_outcome_sequence(rows), "🔴L 🔴L ⚪F 🟢W")
        self.assertEqual(recent_outcome_sequence(["WIN", "LOSS"], limit=1), "🟢W")
        self.assertEqual(recent_outcome_sequence([]), "нет проверенных исходов")
        self.assertEqual(outcome_streak_text(rows), "серия LOSS: 2")
        self.assertEqual(outcome_streak_text(["FLAT", "FLAT", "WIN"]), "серия FLAT: 2")
        self.assertEqual(outcome_streak_text([]), "серии нет")

    def test_action_note_text_is_risk_first(self) -> None:
        self.assertIn("копим данные", action_note_text(3, 90, ["WIN", "WIN"]))
        self.assertIn("серия LOSS", action_note_text(12, 50, ["LOSS", "LOSS", "LOSS", "WIN"]))
        self.assertIn("риск не повышать", action_note_text(15, 80, ["WIN"] * 5))
        self.assertIn("до рабочей выборки", action_note_text(20, 55, ["FLAT", "WIN"]))
        self.assertIn("осторожное преимущество", action_note_text(40, 65, ["WIN", "LOSS"]))
        self.assertIn("качество слабое", action_note_text(40, 40, ["LOSS", "WIN"]))
        self.assertIn("режим наблюдения", action_note_text(40, 52, ["FLAT", "WIN"]))

    def test_pending_check_text_shows_next_or_overdue_check(self) -> None:
        now = datetime(2026, 6, 7, 12, 0, tzinfo=timezone.utc)
        rows = [
            {"status": "PENDING", "due_at": "2026-06-07T12:45:00+00:00"},
            {"status": "PENDING", "due_at": "2026-06-07T12:15:00+00:00"},
            {"status": "WIN", "due_at": "2026-06-07T12:05:00+00:00"},
        ]

        self.assertEqual(pending_check_text([], now), "pending-сигналов нет")
        self.assertEqual(pending_check_text(rows, now), "ближайшая проверка: 12:15 UTC")
        self.assertEqual(
            pending_check_text(rows, datetime(2026, 6, 7, 12, 20, tzinfo=timezone.utc)),
            "просрочены: 1; обнови Win Rate",
        )


if __name__ == "__main__":
    unittest.main()
