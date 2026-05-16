from __future__ import annotations

import unittest

from quant_bot.live_readiness import evaluate_live_readiness, summarize_reconciliations


class LiveReadinessTests(unittest.TestCase):
    def test_blocks_when_evidence_is_too_small(self) -> None:
        result = evaluate_live_readiness(
            {
                "paper_closed_trades": 5,
                "paper_independent_setups": 5,
                "paper_market_setups": 5,
                "paper_profit_factor": 0.8,
                "paper_avg_r": -0.1,
                "testnet_total": 0,
                "testnet_accepted": 0,
                "testnet_reject_rate": 0,
                "daily_loss_limit_pct": 3.0,
                "max_daily_trades": 15,
                "max_open_positions": 3,
                "kill_switch_configured": True,
                "setup_groups": 1,
                "setup_tickers": 1,
                "setup_intervals": 1,
                "setup_strategies": 1,
                "live_orders_enabled": False,
            },
            {
                "min_paper_trades": 100,
                "min_independent_setups": 80,
                "min_market_setups": 100,
                "min_testnet_reconciliations": 25,
                "min_testnet_accepted": 20,
                "max_testnet_reject_rate": 20.0,
                "min_setup_groups": 3,
                "min_profit_factor": 1.2,
                "min_avg_r": 0.0,
                "max_daily_loss_limit_pct": 3.0,
            },
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("Paper-сделок достаточно", result["blockers"])

    def test_summarizes_testnet_reconciliations(self) -> None:
        summary = summarize_reconciliations([
            {"overall": "ACCEPTED"},
            {"overall": "REJECTED"},
            {"overall": "PARTIAL_OR_SKIPPED"},
        ])
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["accepted"], 1)
        self.assertEqual(summary["rejected"], 1)
        self.assertAlmostEqual(summary["reject_rate"], 33.33333333333333)


if __name__ == "__main__":
    unittest.main()
