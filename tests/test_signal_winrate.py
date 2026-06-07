from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quant_bot.signal_winrate import (
    action_note_text,
    basis_counts_text,
    flat_warning_text,
    focus_note_text,
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
    winrate_uncertainty_text,
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

    def test_winrate_uncertainty_text_shows_wilson_interval(self) -> None:
        self.assertEqual(winrate_uncertainty_text(0, 0), "н/д: нет WIN/LOSS")
        self.assertEqual(winrate_uncertainty_text(6, 4), "31.3%–83.2% по 10 WIN/LOSS")
        self.assertEqual(winrate_uncertainty_text("bad", 4), "0.0%–49.0% по 4 WIN/LOSS")

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

    def test_focus_note_text_highlights_best_and_weak_groups(self) -> None:
        buckets = [
            {"label": "BTCUSDT", "counted": 8, "winrate": 75.0, "avg_edge": 0.4},
            {"label": "ETHUSDT", "counted": 7, "winrate": 42.8, "avg_edge": -0.2},
            {"label": "SOLUSDT", "counted": 2, "winrate": 100.0, "avg_edge": 1.0},
        ]

        note = focus_note_text(buckets, min_samples=5)

        self.assertIn("лучше: BTCUSDT WR 75.0% (8, очень мало)", note)
        self.assertIn("слабее: ETHUSDT WR 42.8% (7, очень мало)", note)

    def test_focus_note_text_labels_bucket_group_context(self) -> None:
        buckets = [
            {"group": "ticker", "label": "BTCUSDT", "counted": 8, "winrate": 75.0},
            {"group": "tf", "label": "15м", "counted": 7, "winrate": 42.8},
        ]

        note = focus_note_text(buckets, min_samples=5)

        self.assertIn("актив BTCUSDT", note)
        self.assertIn("TF 15м", note)

    def test_focus_note_text_waits_for_enough_group_data(self) -> None:
        note = focus_note_text([
            {"label": "BTCUSDT", "counted": 2, "winrate": 100.0},
        ], min_samples=5)

        self.assertIn("копим группы", note)
        self.assertIn("минимум 5 WIN/LOSS", note)

    def test_focus_note_text_can_show_single_weak_group(self) -> None:
        note = focus_note_text([
            {"label": "15м", "counted": 6, "winrate": 33.3, "avg_edge": -0.5},
        ], min_samples=5)

        self.assertIn("слабее: 15м WR 33.3% (6, очень мало)", note)

    def test_focus_note_text_marks_working_sample_size(self) -> None:
        note = focus_note_text([
            {"label": "LONG", "counted": 35, "winrate": 62.8, "avg_edge": 0.1},
        ], min_samples=5)

        self.assertIn("лучше: LONG WR 62.8% (35, рабочая)", note)

    def test_flat_warning_text_highlights_no_momentum_group(self) -> None:
        note = flat_warning_text([
            {"group": "tf", "label": "15м", "wins": 1, "losses": 1, "flats": 4},
            {"group": "ticker", "label": "BTCUSDT", "wins": 3, "losses": 2, "flats": 1},
        ], min_samples=5)

        self.assertIn("много FLAT: TF 15м 66.7% (4/6)", note)

    def test_flat_warning_text_waits_for_enough_data_or_no_skew(self) -> None:
        self.assertIn(
            "копим данные",
            flat_warning_text([{"label": "BTCUSDT", "wins": 1, "losses": 0, "flats": 1}], min_samples=5),
        )
        self.assertEqual(
            flat_warning_text([{"label": "BTCUSDT", "wins": 4, "losses": 3, "flats": 1}], min_samples=5),
            "явного тихого перекоса нет",
        )


if __name__ == "__main__":
    unittest.main()
