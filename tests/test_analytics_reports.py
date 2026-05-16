from __future__ import annotations

import unittest

from quant_bot.analytics_reports import (
    calibration_group,
    calibration_stats,
    probability_bucket,
    probability_value,
)


class AnalyticsReportHelperTests(unittest.TestCase):
    def test_probability_value_accepts_percent_and_fraction(self) -> None:
        self.assertAlmostEqual(probability_value(68), 0.68)
        self.assertAlmostEqual(probability_value("0.68"), 0.68)
        self.assertIsNone(probability_value(168))
        self.assertIsNone(probability_value("bad"))

    def test_probability_bucket_groups_forecasts(self) -> None:
        self.assertEqual(probability_bucket(0.681, step=5), "65-70%")
        self.assertEqual(probability_bucket(68.1, step=10), "60-70%")

    def test_calibration_stats_counts_binary_and_neutral_outcomes(self) -> None:
        stats = calibration_stats([
            {"prob": 0.70, "outcome": "win"},
            {"prob": 0.70, "outcome": "loss"},
            {"prob": 0.60, "outcome": "neutral"},
        ])
        self.assertEqual(stats["n"], 3)
        self.assertEqual(stats["binary_n"], 2)
        self.assertEqual(stats["neutral"], 1)
        self.assertAlmostEqual(stats["avg_prob"], 0.70)
        self.assertAlmostEqual(stats["actual_wr"], 0.50)
        self.assertAlmostEqual(stats["gap"], -0.20)

    def test_calibration_group_returns_filtered_groups_and_ece(self) -> None:
        rows = [
            {"prob": 0.70, "bucket": "65-70%", "outcome": "win"},
            {"prob": 0.70, "bucket": "65-70%", "outcome": "loss"},
            {"prob": 0.60, "bucket": "60-65%", "outcome": "loss"},
        ]
        groups, ece = calibration_group(rows, lambda row: row["bucket"], min_n=2)
        self.assertEqual([name for name, _ in groups], ["65-70%"])
        self.assertAlmostEqual(ece, abs(-0.20) * 2 / 3)


if __name__ == "__main__":
    unittest.main()
