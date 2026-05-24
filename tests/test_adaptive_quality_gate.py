from __future__ import annotations

import unittest

from quant_bot.legacy import load_bot_module


def _closed_row(ticker="BTCUSDT", interval="15m", direction="long", strategy="trend_follow_v1", pnl=-1.0):
    return {
        "ticker": ticker,
        "interval": interval,
        "direction": direction,
        "strategy": strategy,
        "status": "CLOSED_LOSS" if pnl < 0 else "CLOSED_WIN",
        "pnl": {
            "status": "ATTRIBUTED",
            "realized_usdt": pnl,
            "outcome": "LOSS" if pnl < 0 else "WIN",
        },
    }


def _candidate(ticker="BTCUSDT", interval="15m", score=88):
    return {
        "ticker": ticker,
        "interval": interval,
        "direction": "long",
        "strategy": "trend_follow_v1",
        "score": score,
        "data": {"price": 100.0},
        "entry_plan": {
            "status": "ENTER_NOW",
            "entry_now_score": score,
            "setup_score": score,
            "score": score,
            "rr_now": 1.67,
        },
    }


class AdaptiveQualityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def test_small_sample_only_observes(self) -> None:
        old_rows = self.bot._adaptive_quality_local_rows_v745
        self.bot._adaptive_quality_local_rows_v745 = lambda chat_id=None, limit=600: [_closed_row() for _ in range(9)]
        try:
            quality = self.bot._adaptive_quality_penalty_v745("chat-1", _candidate())
        finally:
            self.bot._adaptive_quality_local_rows_v745 = old_rows

        self.assertEqual(quality["mode"], "observe")
        self.assertEqual(quality["penalty"], 0)

    def test_weak_history_penalizes_and_can_block_moderate_setup(self) -> None:
        old_rows = self.bot._adaptive_quality_local_rows_v745
        old_base = self.bot._base_testnet_candidate_block_reason_v735_for_v745
        self.bot._adaptive_quality_local_rows_v745 = lambda chat_id=None, limit=600: [_closed_row() for _ in range(10)]
        self.bot._base_testnet_candidate_block_reason_v735_for_v745 = lambda *args, **kwargs: None
        try:
            cand = _candidate(score=88)
            reason = self.bot._testnet_candidate_block_reason_v735(
                "chat-1",
                cand,
                active_positions=[],
                pos_err=None,
                today_count=0,
            )
        finally:
            self.bot._adaptive_quality_local_rows_v745 = old_rows
            self.bot._base_testnet_candidate_block_reason_v735_for_v745 = old_base

        self.assertIn("adaptive quality gate", reason)
        self.assertGreaterEqual(cand["adaptive_quality"]["penalty"], self.bot.ADAPTIVE_GATE_BLOCK_PENALTY_V745)

    def test_strong_current_setup_can_override_adaptive_penalty(self) -> None:
        old_rows = self.bot._adaptive_quality_local_rows_v745
        old_base = self.bot._base_testnet_candidate_block_reason_v735_for_v745
        self.bot._adaptive_quality_local_rows_v745 = lambda chat_id=None, limit=600: [_closed_row() for _ in range(10)]
        self.bot._base_testnet_candidate_block_reason_v735_for_v745 = lambda *args, **kwargs: None
        try:
            cand = _candidate(score=95)
            reason = self.bot._testnet_candidate_block_reason_v735(
                "chat-1",
                cand,
                active_positions=[],
                pos_err=None,
                today_count=0,
            )
        finally:
            self.bot._adaptive_quality_local_rows_v745 = old_rows
            self.bot._base_testnet_candidate_block_reason_v735_for_v745 = old_base

        self.assertIsNone(reason)
        self.assertGreaterEqual(cand["adaptive_quality"]["penalty"], self.bot.ADAPTIVE_GATE_BLOCK_PENALTY_V745)

    def test_candidate_selection_sorts_by_adaptive_score(self) -> None:
        old_tickers = self.bot.PAPER_TRADER_SCAN_TICKERS
        old_tfs = self.bot.PAPER_TRADER_TFS
        old_scan = self.bot._paper_scan_one_v74
        old_penalty = self.bot._adaptive_quality_penalty_v745
        old_open = self.bot._testnet_open_positions_v734
        old_today = self.bot._testnet_today_real_entry_count_v734
        old_base = self.bot._base_testnet_candidate_block_reason_v735_for_v745
        old_context = self.bot.build_futures_context

        def fake_scan(chat_id, ticker, tf):
            score = 95 if ticker == "BADUSDT" else 90
            cand = _candidate(ticker=ticker, interval=tf, score=score)
            row = {
                "ticker": ticker,
                "tf": tf,
                "signal": "LONG",
                "status": "ENTER_NOW",
                "entry_now": score,
                "setup": score,
                "rr": 1.67,
                "gate": "",
            }
            return row, [cand]

        def fake_penalty(chat_id, candidate):
            if candidate.get("ticker") == "BADUSDT":
                return {"mode": "soft_penalty", "penalty": 12, "reasons": ["weak local evidence"], "evidence": []}
            return {"mode": "observe", "penalty": 0, "reasons": [], "evidence": []}

        self.bot.PAPER_TRADER_SCAN_TICKERS = ["BADUSDT", "GOODUSDT"]
        self.bot.PAPER_TRADER_TFS = ["15m"]
        self.bot._paper_scan_one_v74 = fake_scan
        self.bot._adaptive_quality_penalty_v745 = fake_penalty
        self.bot._testnet_open_positions_v734 = lambda: ([], None)
        self.bot._testnet_today_real_entry_count_v734 = lambda chat_id: 0
        self.bot._base_testnet_candidate_block_reason_v735_for_v745 = lambda *args, **kwargs: None
        self.bot.build_futures_context = lambda *args, **kwargs: {}
        try:
            selected, tried = self.bot.testnet_select_trade_candidate("chat-1")
        finally:
            self.bot.PAPER_TRADER_SCAN_TICKERS = old_tickers
            self.bot.PAPER_TRADER_TFS = old_tfs
            self.bot._paper_scan_one_v74 = old_scan
            self.bot._adaptive_quality_penalty_v745 = old_penalty
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_today
            self.bot._base_testnet_candidate_block_reason_v735_for_v745 = old_base
            self.bot.build_futures_context = old_context

        self.assertEqual(selected["ticker"], "GOODUSDT")
        bad_row = next(row for row in tried if row["ticker"] == "BADUSDT")
        self.assertEqual(bad_row["adaptive_quality"]["penalty"], 12)

    def test_adaptive_details_are_stored_but_not_added_to_scan_card(self) -> None:
        row = {
            "ticker": "ETHUSDT",
            "tf": "30m",
            "status": "ENTER_NOW",
            "entry_now": 82,
            "setup": 82,
            "rr": 1.67,
            "adaptive_quality": {"mode": "soft_penalty", "penalty": 6, "reasons": ["tf 30m WR 40% n=10"]},
        }

        payload = self.bot._demo_scan_row_for_storage_v736(row)
        lines = self.bot._format_scan_rows([row])

        self.assertEqual(payload["adaptive_quality"]["penalty"], 6)
        self.assertNotIn("adaptive", lines[0].lower())
        self.assertNotIn("WR", lines[0])


if __name__ == "__main__":
    unittest.main()
