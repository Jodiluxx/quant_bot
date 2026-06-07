from __future__ import annotations

import asyncio
import os
import tempfile

import unittest
from datetime import datetime, timezone

from quant_bot.ui_format import (
    code,
    compact_tf,
    edge_text,
    html_escape,
    scan_status,
    score_bar,
    short_text,
    status_human,
    status_plain,
    winrate_bar,
)
from quant_bot.legacy import load_bot_module


class TelegramUiPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def setUp(self) -> None:
        self._tmp_signal_winrate = tempfile.TemporaryDirectory()
        self._old_signal_winrate_file = self.bot.SIGNAL_WINRATE_STATE_FILE
        self.bot.SIGNAL_WINRATE_STATE_FILE = os.path.join(
            self._tmp_signal_winrate.name,
            "signal_winrate_state.json",
        )

    def tearDown(self) -> None:
        self.bot.SIGNAL_WINRATE_STATE_FILE = self._old_signal_winrate_file
        self._tmp_signal_winrate.cleanup()

    def test_main_keyboard_keeps_expected_callbacks(self) -> None:
        rows = self.bot.main_keyboard()["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        for callback in {"menu_signal", "menu_autobot", "auto_settings"}:
            self.assertIn(callback, callbacks)
        self.assertNotIn("back_main", callbacks)
        for hidden in {"menu_analytics", "menu_positions", "menu_learn", "menu_flow", "get_fg", "entry_point"}:
            self.assertNotIn(hidden, callbacks)

    def test_autobot_keyboard_uses_existing_callbacks(self) -> None:
        rows = self.bot.autobot_keyboard(987654321)["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        for callback in {"paper_run_now", "paper_open_positions", "paper_closed_menu", "auto_settings", "back_main"}:
            self.assertIn(callback, callbacks)
        self.assertIn("wr_page_recent_0", callbacks)
        for hidden in {"setup_analytics", "prob_calibration", "bot_quality", "execution_status", "live_readiness"}:
            self.assertNotIn(hidden, callbacks)

    def test_signal_menu_exposes_all_asset_scan(self) -> None:
        rows = self.bot.signal_menu_keyboard(987654321)["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        self.assertIn("sig_crypto_tickers", callbacks)
        self.assertIn("sig_stock_tickers", callbacks)
        self.assertIn("sig_commodity_tickers", callbacks)
        self.assertNotIn("get_signal", callbacks)
        self.assertNotIn("signal_scan_crypto", callbacks)

    def test_signal_group_screen_has_scan_asset_and_tf_controls(self) -> None:
        rows = self.bot.signal_group_keyboard_v766(987654321, "stocks")["inline_keyboard"]
        callbacks = {button["callback_data"] for row in rows for button in row}
        self.assertIn("get_signal", callbacks)
        self.assertIn("signal_scan_stocks", callbacks)
        self.assertIn("sig_group_asset_stocks", callbacks)
        self.assertIn("sig_group_tf_stocks", callbacks)
        text = self.bot.format_signal_group_menu_text_v766(987654321, "stocks")
        self.assertIn("Акции", text)
        self.assertIn("TF", text)

    def test_signal_group_tf_lists_are_separate(self) -> None:
        crypto_callbacks = [
            button["callback_data"]
            for row in self.bot.signal_group_tf_keyboard_v766(987654321, "crypto")["inline_keyboard"]
            for button in row
        ]
        stock_callbacks = [
            button["callback_data"]
            for row in self.bot.signal_group_tf_keyboard_v766(987654321, "stocks")["inline_keyboard"]
            for button in row
        ]
        self.assertIn("sig_interval_5m", crypto_callbacks)
        self.assertIn("sig_interval_15m", crypto_callbacks)
        self.assertNotIn("sig_interval_5m", stock_callbacks)
        self.assertNotIn("sig_interval_15m", stock_callbacks)
        self.assertIn("sig_interval_1h", stock_callbacks)

    def test_signal_card_is_compact_and_html_escapes_dynamic_text(self) -> None:
        text = self.bot.format_signal_summary(
            {
                "signal": "🟢 LONG",
                "direction": "long",
                "price": 100.0,
                "confidence": 81,
                "prob": 0.68,
                "strategy": "Pullback <test>",
                "bull_weight_sum": 8.0,
                "bear_weight_sum": 3.0,
                "vol_ratio": 1.4,
                "regime": "trend",
                "bull_args": ["Цена > EMA20"],
                "bear_args": ["Цена < EMA200"],
                "risk_levels": {"sl": 98.0, "tp1": 103.0, "tp2": 105.0, "rr_ratio": 1.7},
                "entry_plan": {
                    "status": "WAIT_RETEST",
                    "entry_now_score": 69,
                    "setup_score": 81,
                    "rr_now": 1.7,
                    "orderflow_state": "neutral",
                },
            },
            "BTCUSDT",
            "15m",
        )
        self.assertIn("АНАЛИЗ АКТИВА: #BTCUSDT [15м]", text)
        self.assertIn("ВЕРДИКТ: WAIT", text)
        self.assertIn("Идея: <b>LONG</b>", text)
        self.assertIn("Сила паттерна: <b>81/100</b>", text)
        self.assertIn("ждать ретест", text)
        self.assertIn("WAIT", text)
        self.assertIn("не считается без сделки", text)
        self.assertIn("<code>$100.0000</code>", text)
        self.assertNotIn("n/a", text)
        self.assertIn("Цена &lt; EMA200", text)
        self.assertLessEqual(len(text.splitlines()), 28)

    def test_scan_rows_are_limited_and_readable(self) -> None:
        rows = [{"ticker": "ETHUSDT", "tf": "30m", "status": "WAIT_RETEST", "entry_now": n, "setup": n, "rr": 1.67} for n in range(10)]
        lines = self.bot._format_scan_rows(rows)
        self.assertEqual(len(lines), 5)
        self.assertIn("WAIT RETEST", lines[0])

    def test_simple_mode_blocks_hidden_old_callbacks(self) -> None:
        self.assertTrue(self.bot.simple_public_mode_enabled())
        for callback in {"menu_analytics", "execution_status", "sig_analysis", "market_heatmap"}:
            self.assertTrue(self.bot._simple_hidden_callback_v731(callback))
        for callback in {"menu_signal", "menu_autobot", "paper_run_now", "auto_settings", "runtime_diagnostics"}:
            self.assertFalse(self.bot._simple_hidden_callback_v731(callback))

    def test_auto_signal_defaults_scan_all_tf_every_5m(self) -> None:
        chat_id = "auto-defaults-v752"
        st = self.bot._get_auto_task_settings(chat_id, "signals")
        st["send_interval"] = "30m"
        st["tf"] = "30m"

        self.bot._simple_sync_public_auto_settings(chat_id)

        self.assertEqual(st["send_interval"], "5m")
        self.assertIsNone(st["tf"])
        self.assertEqual(self.bot.PAPER_TRADER_TFS, self.bot.AUTO_SIGNAL_SCAN_TFS_V752)
        self.assertIn("4h", self.bot.AUTO_SIGNAL_SCAN_TFS_V752)
        rows = self.bot.auto_task_keyboard(chat_id, "signals")["inline_keyboard"]
        callbacks = [button["callback_data"] for row in rows for button in row]
        self.assertNotIn("auto_choose_iv_signals", callbacks)

    def test_auto_signal_scan_is_silent_when_no_actionable_signal(self) -> None:
        old_tickers = self.bot.PAPER_TRADER_SCAN_TICKERS
        old_tfs = self.bot.AUTO_SIGNAL_SCAN_TFS_V752
        old_paper_tfs = self.bot.PAPER_TRADER_TFS
        old_scan = self.bot._paper_scan_one_v74
        old_open = self.bot._testnet_open_positions_v734
        old_today = self.bot._testnet_today_real_entry_count_v734
        old_auto_tickers = self.bot._auto_signal_scan_tickers_v764
        calls = []

        def fake_scan(chat_id, ticker, tf):
            calls.append((ticker, tf))
            return {
                "ticker": ticker,
                "tf": tf,
                "status": "WAIT_RETEST",
                "entry_now": 50,
                "setup": 70,
                "rr": 1.6,
            }, []

        self.bot.PAPER_TRADER_SCAN_TICKERS = ["BTCUSDT"]
        self.bot.AUTO_SIGNAL_SCAN_TFS_V752 = ["5m", "15m", "4h"]
        self.bot.PAPER_TRADER_TFS = ["5m", "15m", "4h"]
        self.bot._paper_scan_one_v74 = fake_scan
        self.bot._testnet_open_positions_v734 = lambda: ([], None)
        self.bot._testnet_today_real_entry_count_v734 = lambda chat_id=None: 0
        self.bot._auto_signal_scan_tickers_v764 = lambda now_utc=None: ["BTCUSDT"]
        try:
            msg = self.bot.build_auto_signals_message("auto-silent-v752")
        finally:
            self.bot.PAPER_TRADER_SCAN_TICKERS = old_tickers
            self.bot.AUTO_SIGNAL_SCAN_TFS_V752 = old_tfs
            self.bot.PAPER_TRADER_TFS = old_paper_tfs
            self.bot._paper_scan_one_v74 = old_scan
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_today
            self.bot._auto_signal_scan_tickers_v764 = old_auto_tickers

        self.assertIsNone(msg)
        self.assertCountEqual(calls, [("BTCUSDT", "5m"), ("BTCUSDT", "15m"), ("BTCUSDT", "4h")])

    def test_auto_signal_sends_best_actionable_multi_tf_candidate(self) -> None:
        old_tickers = self.bot.PAPER_TRADER_SCAN_TICKERS
        old_tfs = self.bot.AUTO_SIGNAL_SCAN_TFS_V752
        old_paper_tfs = self.bot.PAPER_TRADER_TFS
        old_scan = self.bot._paper_scan_one_v74
        old_open = self.bot._testnet_open_positions_v734
        old_today = self.bot._testnet_today_real_entry_count_v734
        old_plan = self.bot._build_testnet_trade_plan_v734
        old_auto_tickers = self.bot._auto_signal_scan_tickers_v764
        old_submit = self.bot._submit_testnet_trade_v734
        submit_calls = []

        def fake_scan(chat_id, ticker, tf):
            row = {
                "ticker": ticker,
                "tf": tf,
                "status": "ENTER_NOW" if tf == "4h" else "WAIT_RETEST",
                "entry_now": 88 if tf == "4h" else 40,
                "setup": 90 if tf == "4h" else 60,
                "rr": 1.8 if tf == "4h" else 1.2,
            }
            if tf != "4h":
                return row, []
            data = {
                "signal": "LONG",
                "direction": "long",
                "price": 100.0,
                "confidence": 82,
                "prob": 0.68,
                "bull_args": ["Цена > EMA20"],
                "bear_args": ["Цена внутри Bollinger Bands"],
                "risk_levels": {"sl": 98.0, "tp1": 103.0, "tp2": 105.0, "rr_ratio": 1.8},
                "risk_blockers": [],
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 88,
                    "setup_score": 90,
                    "rr_now": 1.8,
                    "sl": 98.0,
                    "tp1": 103.0,
                    "tp2": 105.0,
                },
            }
            candidate = {
                "ticker": ticker,
                "interval": tf,
                "direction": "long",
                "strategy": "strict_quality_v1",
                "score": 110,
                "data": data,
                "entry_plan": data["entry_plan"],
                "reason": "strict quality test",
            }
            return row, [candidate]

        self.bot.PAPER_TRADER_SCAN_TICKERS = ["BTCUSDT"]
        self.bot.AUTO_SIGNAL_SCAN_TFS_V752 = ["5m", "4h"]
        self.bot.PAPER_TRADER_TFS = ["5m", "4h"]
        self.bot._paper_scan_one_v74 = fake_scan
        self.bot._testnet_open_positions_v734 = lambda: ([], None)
        self.bot._testnet_today_real_entry_count_v734 = lambda chat_id=None: 0
        self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: {"blockers": []}
        self.bot._auto_signal_scan_tickers_v764 = lambda now_utc=None: ["BTCUSDT"]
        self.bot._submit_testnet_trade_v734 = lambda chat_id, candidate: submit_calls.append((chat_id, candidate)) or {
            "ok": True,
            "stage": "done",
            "plan": {
                "ticker": candidate["ticker"],
                "interval": candidate["interval"],
                "direction": candidate["direction"],
                "entry_order": {"entry_reference": 100.0, "leverage": 10},
            },
            "protection": {"orders": [{"label": "SL"}, {"label": "TP1"}]},
            "monitor": {"status": "PROTECTED", "sl_count": 1, "tp_count": 1},
        }
        try:
            msg = self.bot.build_auto_signals_message("auto-ready-v752")
        finally:
            self.bot.PAPER_TRADER_SCAN_TICKERS = old_tickers
            self.bot.AUTO_SIGNAL_SCAN_TFS_V752 = old_tfs
            self.bot.PAPER_TRADER_TFS = old_paper_tfs
            self.bot._paper_scan_one_v74 = old_scan
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_today
            self.bot._build_testnet_trade_plan_v734 = old_plan
            self.bot._auto_signal_scan_tickers_v764 = old_auto_tickers
            self.bot._submit_testnet_trade_v734 = old_submit

        self.assertIsNotNone(msg)
        self.assertIn("Авто-сигнал", msg)
        self.assertIn("BTCUSDT", msg)
        self.assertIn("LONG", msg)
        self.assertIn("Win Rate", msg)
        self.assertNotIn("WAIT", msg.splitlines()[0])
        self.assertEqual(len(submit_calls), 0)
        rows = self.bot._signal_winrate_rows_v777("auto-ready-v752", limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ticker"], "BTCUSDT")
        self.assertEqual(rows[0]["status"], "PENDING")

    def test_auto_signal_records_even_when_demo_trade_gate_would_block_candidate(self) -> None:
        old_tickers = self.bot.PAPER_TRADER_SCAN_TICKERS
        old_tfs = self.bot.AUTO_SIGNAL_SCAN_TFS_V752
        old_paper_tfs = self.bot.PAPER_TRADER_TFS
        old_scan = self.bot._paper_scan_one_v74
        old_open = self.bot._testnet_open_positions_v734
        old_today = self.bot._testnet_today_real_entry_count_v734
        old_plan = self.bot._build_testnet_trade_plan_v734
        old_auto_tickers = self.bot._auto_signal_scan_tickers_v764

        def fake_scan(chat_id, ticker, tf):
            data = {
                "signal": "SHORT",
                "direction": "short",
                "price": 1.0,
                "confidence": 86,
                "prob": 0.71,
                "bull_args": ["test"],
                "bear_args": ["test"],
                "risk_levels": {"sl": 1.02, "tp1": 0.97, "tp2": 0.95, "rr_ratio": 1.67},
                "risk_blockers": [],
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 97,
                    "setup_score": 97,
                    "rr_now": 1.67,
                },
            }
            candidate = {
                "ticker": ticker,
                "interval": tf,
                "direction": "short",
                "strategy": "strict_quality_v1",
                "score": 120,
                "data": data,
                "entry_plan": data["entry_plan"],
                "reason": "strong test setup",
            }
            return {
                "ticker": ticker,
                "tf": tf,
                "status": "ENTER_NOW",
                "entry_now": 97,
                "setup": 97,
                "rr": 1.67,
            }, [candidate]

        self.bot.PAPER_TRADER_SCAN_TICKERS = ["XRPUSDT"]
        self.bot.AUTO_SIGNAL_SCAN_TFS_V752 = ["45m"]
        self.bot.PAPER_TRADER_TFS = ["45m"]
        self.bot._paper_scan_one_v74 = fake_scan
        self.bot._testnet_open_positions_v734 = lambda: ([{}] * self.bot.PAPER_TRADER_MAX_POSITIONS, None)
        self.bot._testnet_today_real_entry_count_v734 = lambda chat_id=None: 0
        self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: {"blockers": []}
        self.bot._auto_signal_scan_tickers_v764 = lambda now_utc=None: ["XRPUSDT"]
        try:
            msg = self.bot.build_auto_signals_message("auto-blocked-v753")
        finally:
            self.bot.PAPER_TRADER_SCAN_TICKERS = old_tickers
            self.bot.AUTO_SIGNAL_SCAN_TFS_V752 = old_tfs
            self.bot.PAPER_TRADER_TFS = old_paper_tfs
            self.bot._paper_scan_one_v74 = old_scan
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_today
            self.bot._build_testnet_trade_plan_v734 = old_plan
            self.bot._auto_signal_scan_tickers_v764 = old_auto_tickers

        self.assertIsNotNone(msg)
        self.assertIn("XRPUSDT", msg)
        self.assertIn("Win Rate", msg)
        rows = self.bot._signal_winrate_rows_v777("auto-blocked-v753", limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["direction"], "SHORT")

    def test_signal_winrate_evaluates_direction_after_own_timeframe(self) -> None:
        row, created = self.bot._signal_winrate_record_v777(
            "wr-chat",
            "BTCUSDT",
            "5m",
            "LONG",
            100.0,
            source="unit",
        )
        self.assertTrue(created)
        old_price = self.bot.get_price
        try:
            self.bot.get_price = lambda ticker: 101.0
            due = self.bot._signal_winrate_parse_dt_v777(row["due_at"])
            completed = self.bot._signal_winrate_evaluate_pending_v777("wr-chat", now=due)
        finally:
            self.bot.get_price = old_price

        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["status"], "WIN")
        self.assertGreater(completed[0]["result_edge_pct"], 0)
        stats = self.bot._signal_winrate_stats_v777("wr-chat")
        self.assertEqual(stats["wins"], 1)
        self.assertEqual(stats["winrate"], 100.0)

    def test_signal_winrate_report_breaks_down_by_ticker_tf_and_direction(self) -> None:
        self.bot._signal_winrate_save_v777({
            "signals": [
                {
                    "id": "btc-win-1",
                    "chat_id": "wr-breakdown",
                    "ticker": "BTCUSDT",
                    "direction": "LONG",
                    "interval": "15m",
                    "created_at": "2026-06-04T00:00:00+00:00",
                    "due_at": "2026-06-04T00:15:00+00:00",
                    "status": "WIN",
                    "entry_price": 100.0,
                    "exit_price": 101.0,
                    "result_edge_pct": 1.0,
                },
                {
                    "id": "btc-win-2",
                    "chat_id": "wr-breakdown",
                    "ticker": "BTCUSDT",
                    "direction": "LONG",
                    "interval": "15m",
                    "created_at": "2026-06-04T01:00:00+00:00",
                    "due_at": "2026-06-04T01:15:00+00:00",
                    "status": "WIN",
                    "entry_price": 100.0,
                    "exit_price": 102.0,
                    "result_edge_pct": 2.0,
                },
                {
                    "id": "eth-loss",
                    "chat_id": "wr-breakdown",
                    "ticker": "ETHUSDT",
                    "direction": "SHORT",
                    "interval": "30m",
                    "created_at": "2026-06-04T02:00:00+00:00",
                    "due_at": "2026-06-04T02:30:00+00:00",
                    "status": "LOSS",
                    "entry_price": 100.0,
                    "exit_price": 101.0,
                    "result_edge_pct": -1.0,
                },
            ]
        })

        text = self.bot.format_signal_winrate_report_v777("wr-breakdown", evaluate=False)

        self.assertIn("По активам", text)
        self.assertIn("По TF", text)
        self.assertIn("По направлению", text)
        self.assertIn("BTCUSDT", text)
        self.assertIn("15м", text)
        self.assertIn("LONG", text)
        self.assertIn("данных мало", text)
        self.assertIn("🟢 2 WIN | 🔴 1 LOSS | ⚪ 0 FLAT", text)

    def test_signal_winrate_history_is_paginated(self) -> None:
        rows = []
        for idx in range(8):
            rows.append({
                "id": f"sig-{idx}",
                "chat_id": "wr-pages",
                "ticker": "BTCUSDT",
                "direction": "LONG",
                "interval": "15m",
                "created_at": f"2026-06-04T0{idx}:00:00+00:00",
                "due_at": f"2026-06-04T0{idx}:15:00+00:00",
                "status": "WIN" if idx % 2 else "LOSS",
                "entry_price": 100.0 + idx,
                "exit_price": 101.0 + idx,
                "result_edge_pct": 1.0 if idx % 2 else -1.0,
            })
        self.bot._signal_winrate_save_v777({"signals": rows})

        text = self.bot.format_signal_winrate_page_v781("wr-pages", "recent", 1)
        keyboard = self.bot.signal_winrate_page_keyboard_v781("wr-pages", "recent", 1)
        callbacks = {button["callback_data"] for row in keyboard["inline_keyboard"] for button in row}

        self.assertIn("История сигналов", text)
        self.assertIn("Стр. <b>2/2</b>", text)
        self.assertIn("BTCUSDT", text)
        self.assertIn("wr_page_recent_0", callbacks)
        self.assertIn("wr_page_recent_1", callbacks)

    def test_signal_tabs_use_cached_signal_data(self) -> None:
        chat_id = "signal-tabs"
        old_tickers = dict(self.bot.user_tickers)
        old_intervals = dict(self.bot.user_intervals)
        old_cache = dict(self.bot._SIGNAL_DETAIL_CACHE)
        try:
            self.bot.user_tickers[chat_id] = "BTCUSDT"
            self.bot.user_intervals[chat_id] = "15m"
            data = {
                "signal": "LONG",
                "direction": "long",
                "price": 100.0,
                "confidence": 82,
                "vol_ratio": 1.2,
                "regime": "trend",
                "risk_levels": {"sl": 98.0, "tp1": 103.0, "rr_ratio": 1.7},
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 86,
                    "setup_score": 88,
                    "rr_now": 1.7,
                    "entry_gate_reason": "score и защитные фильтры разрешают вход сейчас",
                },
                "futures_context": {
                    "funding_rate_pct": 0.01,
                    "open_interest_usdt": 1000000,
                    "basis_pct": 0.02,
                    "warnings": [],
                },
            }
            self.bot._cache_signal_data(chat_id, "BTCUSDT", "15m", data)

            entry_text = self.bot.format_signal_entry_tab_v781(chat_id)
            context_text = self.bot.format_signal_context_tab_v781(chat_id)
            callbacks = {
                button["callback_data"]
                for row in self.bot.compact_signal_keyboard()["inline_keyboard"]
                for button in row
            }
        finally:
            self.bot.user_tickers.clear()
            self.bot.user_tickers.update(old_tickers)
            self.bot.user_intervals.clear()
            self.bot.user_intervals.update(old_intervals)
            self.bot._SIGNAL_DETAIL_CACHE.clear()
            self.bot._SIGNAL_DETAIL_CACHE.update(old_cache)

        self.assertIn("Вход: #BTCUSDT [15м]", entry_text)
        self.assertIn("EntryNow: <b>86/100</b>", entry_text)
        self.assertIn("Контекст: #BTCUSDT [15м]", context_text)
        self.assertIn("Funding", context_text)
        self.assertIn("signal_tab_entry", callbacks)
        self.assertIn("signal_tab_context", callbacks)

    def test_extracted_ui_format_helpers_match_legacy_wrappers(self) -> None:
        self.assertEqual(html_escape("A&B < C > D"), "A&amp;B &lt; C &gt; D")
        self.assertEqual(html_escape("A&B < C > D"), self.bot._ui_html("A&B < C > D"))
        self.assertEqual(short_text("one\n two   three", 32), "one two three")
        self.assertEqual(short_text("abcdef", 4), "abc…")
        self.assertEqual(code("BTC<USDT>"), self.bot._ui_code_v779("BTC<USDT>"))
        self.assertEqual(compact_tf("45m"), self.bot._ui_tf_short("45m"))
        self.assertEqual(compact_tf("1h"), self.bot._ui_tf_short("1h"))
        self.assertEqual(status_plain("WAIT_RETEST"), self.bot._ui_status_plain("WAIT_RETEST"))
        self.assertEqual(status_plain("ENTER_NOW"), "READY")
        self.assertEqual(status_human("WAIT_RETEST"), self.bot._ui_status_human_v779("WAIT_RETEST"))
        self.assertEqual(scan_status("SHORT"), self.bot._ui_scan_status_v779("SHORT"))
        self.assertEqual(score_bar(81), self.bot._ui_score_bar_v780(81))
        self.assertEqual(score_bar("bad"), "⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜")
        self.assertEqual(winrate_bar(None), "⬜⬜⬜⬜⬜⬜⬜⬜")
        self.assertEqual(winrate_bar(50), self.bot._signal_winrate_bar_v779(50))
        self.assertEqual(edge_text(1.25), self.bot._signal_winrate_edge_text_v779(1.25))
        self.assertEqual(edge_text("bad"), "⚪ н/д")

    def test_single_message_navigation_helpers_are_registered(self) -> None:
        self.assertEqual(self.bot.BOT_VERSION_LABEL, "v7.86 Signal Keyboard Helper Extraction")
        self.assertTrue(callable(self.bot.async_edit_message_text))
        self.assertTrue(callable(self.bot.send_or_edit))
        self.assertIn("async_edit_message_text", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("send_or_edit", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("auto_signal_scan_candidates", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("auto_signal_select_trade_candidate", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_stage_error", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_sync_server_time", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_timestamp_ms", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("runtime_bot_runtime_path", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("runtime_bot_processes", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("runtime_latest_chain", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_runtime_diagnostics", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_signal_scan_all", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_scan_all_keyboard", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_last_trade_attempt", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("last_trade_attempt_keyboard", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("get_fear_greed", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("prune_runtime_caches", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("record_testnet_journal_event", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("humanize_testnet_reason", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("synced_testnet_signal_candidate", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_protection_labels", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_lifecycle_public_status", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_winrate_record", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_winrate_evaluate_pending", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_winrate_stats", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_winrate_bucket_stats", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_signal_winrate_report", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_signal_winrate_page", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_signal_entry_tab", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_signal_context_tab", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_score_bar", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_winrate_bar", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_edge_text", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_html", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_code", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_tf_short", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_status_plain", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_status_human", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("ui_scan_status", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_exploration_data_block", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("nyse_is_open", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("commodities_market_is_open", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("stock_ohlcv", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("alpaca_ohlcv", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("alpaca_price", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("alpaca_enabled_for_ticker", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("oanda_ohlcv", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("oanda_price", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("oanda_enabled_for_ticker", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("auto_signal_scan_tickers", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("auto_signal_scan_pairs", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_group_keyboard", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("signal_group_tf_keyboard", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertTrue(any(layer[0] == "v7.32" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.33" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.34" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.35" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.36" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.37" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.38" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.39" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.40" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.41" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.42" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.43" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.44" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.45" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.46" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.47" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.48" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.49" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.50" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.51" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.52" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.53" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.54" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.55" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.56" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.57" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.58" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.59" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.60" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.61" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.62" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.63" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.64" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.65" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.66" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.67" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.68" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.69" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.70" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.71" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.72" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.73" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.74" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.75" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.76" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.77" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.78" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.79" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.80" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.81" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.82" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.83" for layer in self.bot.RUNTIME_LAYERS))
        self.assertTrue(any(layer[0] == "v7.84" for layer in self.bot.RUNTIME_LAYERS))
        self.assertIn("testnet_select_trade_candidate", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("demo_analysis_record_cycle", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("run_immediate_testnet_monitor", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_public_stats", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_ui_cached_call", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_open_positions_ui", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_income_stats_ui", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_lifecycle_recent_ui", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_closed_trade_rows_ui", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("normalize_testnet_plan", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_connection_status", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("rebuild_testnet_lifecycle", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("cancel_testnet_open_orders", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("cancel_testnet_algo_orders", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_auto_safety_after_monitor", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("submit_testnet_emergency_close_position", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_closed_trade_rows", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_pnl_attribution", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_position_quality", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("format_testnet_lifecycle_report", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("testnet_lifecycle_display_status", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("adaptive_quality_stats", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("adaptive_quality_penalty", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("adaptive_quality_penalty_from_stats", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("adaptive_quality_row_is_fresh", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("adaptive_quality_bucket_group", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("adaptive_quality_adjusted_winrate", self.bot.ACTIVE_RUNTIME_FUNCTIONS)
        self.assertIn("submit_testnet_trade", self.bot.ACTIVE_RUNTIME_FUNCTIONS)

    def test_demo_cycle_uses_plain_human_execution_language(self) -> None:
        old_selector = self.bot._auto_signal_select_trade_candidate_v753
        old_price = self.bot.get_price
        try:
            data = {
                "signal": "LONG",
                "direction": "long",
                "price": 100.0,
                "confidence": 82,
                "prob": 0.68,
                "bull_args": ["test"],
                "bear_args": ["test"],
                "risk_levels": {"sl": 98.0, "tp1": 103.0, "tp2": 105.0, "rr_ratio": 1.67},
                "risk_blockers": [],
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 88,
                    "setup_score": 90,
                    "rr_now": 1.67,
                    "sl": 98.0,
                    "tp1": 103.0,
                    "tp2": 105.0,
                },
            }
            candidate = {
                "ticker": "BTCUSDT",
                "interval": "15m",
                "direction": "long",
                "strategy": "strict_quality_v1",
                "reason": "strict quality test",
                "data": data,
                "entry_plan": data["entry_plan"],
            }
            self.bot._auto_signal_select_trade_candidate_v753 = lambda chat_id: (candidate, [])
            self.bot.get_price = lambda ticker: 100.0
            text = self.bot.paper_trader_cycle("human-demo", manual=True)
        finally:
            self.bot._auto_signal_select_trade_candidate_v753 = old_selector
            self.bot.get_price = old_price

        self.assertIn("Ордера не отправляются", text)
        self.assertIn("Записал новый сигнал", text)
        self.assertIn("BTCUSDT", text)
        self.assertIn("Win Rate", text)
        self.assertNotIn("reduce-only", text)
        self.assertNotIn("Protection:", text)
        self.assertNotIn("Monitor:", text)
        rows = self.bot._signal_winrate_rows_v777("human-demo", limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "PENDING")

    def test_last_trade_attempt_report_explains_risk_gate_and_chain(self) -> None:
        old_cycles = self.bot._demo_analysis_recent_cycles_v736
        old_chain = self.bot._runtime_latest_chain_v755
        try:
            self.bot._demo_analysis_recent_cycles_v736 = lambda chat_id=None, limit=10: [
                {
                    "ts": "2026-06-02T17:36:00+00:00",
                    "user_visible": {
                        "status": "NO_TRADE",
                        "reason": "Лучший сетап WAIT RETEST, но Testnet-gate остановил вход",
                    },
                    "selected": {
                        "ticker": "XRPUSDT",
                        "direction": "short",
                        "interval": "15m",
                        "entry_now": 69,
                        "setup": 74,
                    },
                    "result": {"stage": "gate"},
                    "scan": {
                        "total_rows": 42,
                        "top": [
                            {
                                "ticker": "XRPUSDT",
                                "tf": "15m",
                                "status": "WAIT RETEST",
                                "entry_now": 69,
                                "setup": 74,
                            }
                        ],
                    },
                }
            ]
            self.bot._runtime_latest_chain_v755 = lambda chat_id=None: {
                "plan": {"ticker": "BNBUSDT", "direction": "long", "interval": "15m"},
                "events": [
                    {"type": "testnet_order_test", "ok": True, "submitted": True},
                    {
                        "type": "testnet_protection_order_test",
                        "ok": False,
                        "submitted": True,
                        "reason": "protection price is invalid",
                    },
                ],
            }

            text = self.bot.format_last_trade_attempt_v760(987654321)
        finally:
            self.bot._demo_analysis_recent_cycles_v736 = old_cycles
            self.bot._runtime_latest_chain_v755 = old_chain

        self.assertIn("Последняя попытка", text)
        self.assertIn("Проверено: <b>42</b>", text)
        self.assertIn("XRP", text)
        self.assertIn("NO_TRADE", text)
        self.assertIn("Entry test", text)
        self.assertIn("OK", text)
        self.assertIn("Protection test", text)
        self.assertIn("FAIL", text)
        self.assertIn("не ошибка Binance", text)

    def test_runtime_diagnostics_shows_duplicate_processes_and_stage_gap(self) -> None:
        old_processes = self.bot._runtime_bot_processes_v755
        old_state = self.bot._execution_load_state_v715
        old_mode = self.bot.execution_mode
        old_short_status = self.bot._testnet_short_status_v733
        old_time_sync = self.bot._testnet_sync_server_time_v758
        try:
            self.bot._runtime_bot_processes_v755 = lambda: [
                {"pid": 111, "current": True, "command": "python bot_runtime.py"},
                {"pid": 222, "current": False, "command": "python bot_runtime.py"},
            ]
            self.bot._execution_load_state_v715 = lambda: {
                "plans": [
                    {
                        "plan_id": "diag-plan-1",
                        "chat_id": "987654321",
                        "ticker": "BNBUSDT",
                        "interval": "4h",
                        "direction": "short",
                        "created_at": "2026-05-26T14:45:00+00:00",
                    }
                ],
                "events": [
                    {
                        "type": "testnet_order_test",
                        "plan_id": "diag-plan-1",
                        "chat_id": "987654321",
                        "ok": True,
                        "ts": "2026-05-26T14:45:01+00:00",
                    }
                ],
            }
            self.bot.execution_mode = lambda: {
                "mode": "testnet",
                "testnet_keys_present": True,
                "testnet_submit_requested": True,
                "testnet_real_submit_requested": True,
            }
            self.bot._testnet_short_status_v733 = lambda: "READY"
            self.bot._testnet_sync_server_time_v758 = lambda force=False: {"offset_ms": -1200, "error": None}
            text = self.bot.format_runtime_diagnostics(987654321)
        finally:
            self.bot._runtime_bot_processes_v755 = old_processes
            self.bot._execution_load_state_v715 = old_state
            self.bot.execution_mode = old_mode
            self.bot._testnet_short_status_v733 = old_short_status
            self.bot._testnet_sync_server_time_v758 = old_time_sync

        self.assertNotIn("Runtime:", text)
        self.assertNotIn("v7.59", text)
        self.assertIn("PID", text)
        self.assertIn("<b>2</b>", text)
        self.assertIn("Time sync", text)
        self.assertIn("BNB", text)
        self.assertIn("entry-test", text)
        self.assertIn("real-entry", text)
        self.assertIn("entry:OK", text)
        self.assertIn("real:--", text)

    def test_signal_scan_all_formats_every_asset_compactly(self) -> None:
        old_tickers = self.bot.PAPER_TRADER_SCAN_TICKERS
        old_interval = dict(self.bot.user_intervals)
        old_scan = self.bot._signal_scan_one_asset_v759
        old_auto_tickers = self.bot._auto_signal_scan_tickers_v764
        try:
            self.bot.PAPER_TRADER_SCAN_TICKERS = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
            self.bot._auto_signal_scan_tickers_v764 = lambda now_utc=None: ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
            self.bot.user_intervals["scan-all-test"] = "1h"

            def fake_scan(chat_id, ticker, interval):
                decisions = {"BTCUSDT": "WAIT", "ETHUSDT": "LONG", "XRPUSDT": "SHORT"}
                return {"ticker": ticker, "interval": interval, "decision": decisions[ticker], "reason": "test"}

            self.bot._signal_scan_one_asset_v759 = fake_scan
            text = self.bot.format_signal_scan_all_v759("scan-all-test")
        finally:
            self.bot.PAPER_TRADER_SCAN_TICKERS = old_tickers
            self.bot.user_intervals.clear()
            self.bot.user_intervals.update(old_interval)
            self.bot._signal_scan_one_asset_v759 = old_scan
            self.bot._auto_signal_scan_tickers_v764 = old_auto_tickers

        self.assertIn("Проверено: <b>3/3</b>", text)
        self.assertIn("<code>BTCUSDT</code> — <b>WAIT</b>", text)
        self.assertIn("<code>ETHUSDT</code> — <b>LONG</b>", text)
        self.assertIn("<code>XRPUSDT</code> — <b>SHORT</b>", text)

    def test_stock_and_commodity_universe_is_signal_only_and_session_gated(self) -> None:
        self.assertEqual(self.bot.STOCK_SIGNAL_TICKERS_V764, ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL"])
        self.assertEqual(self.bot.COMMODITY_SIGNAL_TICKERS_V765, ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "USOIL", "UKOIL", "COPPER"])
        self.assertEqual(self.bot.YAHOO_SIGNAL_SYMBOLS_V765["XAUUSD"], "GC=F")
        self.assertEqual(self.bot.YAHOO_SIGNAL_SYMBOLS_V765["XAGUSD"], "SI=F")
        self.assertFalse(any(ticker in self.bot.PAPER_TRADER_SCAN_TICKERS for ticker in self.bot.STOCK_SIGNAL_TICKERS_V764))
        self.assertFalse(any(ticker in self.bot.PAPER_TRADER_SCAN_TICKERS for ticker in self.bot.COMMODITY_SIGNAL_TICKERS_V765))
        self.assertEqual(self.bot.DELAYED_YAHOO_SIGNAL_TFS_V765, ["30m", "45m", "1h", "4h"])
        self.assertNotIn("5m", self.bot.DELAYED_YAHOO_SIGNAL_TFS_V765)
        self.assertNotIn("15m", self.bot.DELAYED_YAHOO_SIGNAL_TFS_V765)

        old_force = os.environ.pop("STOCK_SIGNALS_FORCE_NYSE_OPEN", None)
        old_commodity_force = os.environ.pop("COMMODITY_SIGNALS_FORCE_OPEN", None)
        try:
            before_open = datetime(2026, 6, 3, 13, 0, tzinfo=timezone.utc)
            regular_session = datetime(2026, 6, 3, 14, 30, tzinfo=timezone.utc)
            saturday = datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc)
            self.assertFalse(self.bot.nyse_is_open_v764(before_open))
            self.assertTrue(self.bot.nyse_is_open_v764(regular_session))
            self.assertTrue(self.bot.commodities_market_is_open_v765(before_open))
            self.assertFalse(self.bot.commodities_market_is_open_v765(saturday))
            self.assertNotIn("AAPL", self.bot._auto_signal_scan_tickers_v764(before_open))
            self.assertIn("XAUUSD", self.bot._auto_signal_scan_tickers_v764(before_open))
            self.assertIn("AAPL", self.bot._auto_signal_scan_tickers_v764(regular_session))
            self.assertNotIn("XAUUSD", self.bot._auto_signal_scan_tickers_v764(saturday))
        finally:
            if old_force is not None:
                os.environ["STOCK_SIGNALS_FORCE_NYSE_OPEN"] = old_force
            if old_commodity_force is not None:
                os.environ["COMMODITY_SIGNALS_FORCE_OPEN"] = old_commodity_force

    def test_delayed_commodity_signal_card_labels_yahoo_proxy_source(self) -> None:
        old_oanda = os.environ.pop("OANDA_API_TOKEN", None)
        old_oanda_alt = os.environ.pop("OANDA_TOKEN", None)
        data = {
            "signal": "LONG",
            "direction": "long",
            "price": 4496.10,
            "confidence": 80,
            "prob": 0.68,
            "bull_args": ["test support"],
            "bear_args": ["test risk"],
            "risk_levels": {
                "entry": 4496.10,
                "sl": 4475.83,
                "tp1": 4530.42,
                "tp2": 4550.90,
                "rr_ratio": 1.67,
            },
            "entry_plan": {
                "status": "ENTER_NOW",
                "entry_now_score": 78,
                "setup_score": 80,
                "rr_now": 1.67,
            },
        }
        try:
            text = self.bot.format_signal_summary(data, "XAUUSD", "45m")
            self.assertIn("XAUUSD", text)
            self.assertIn("Yahoo futures proxy", text)
            self.assertIn("GC=F", text)
            self.assertIn("не OANDA spot", text)
        finally:
            if old_oanda is not None:
                os.environ["OANDA_API_TOKEN"] = old_oanda
            if old_oanda_alt is not None:
                os.environ["OANDA_TOKEN"] = old_oanda_alt

    def test_oanda_commodity_source_enables_fast_timeframes_and_card_label(self) -> None:
        old_token = os.environ.get("OANDA_API_TOKEN")
        try:
            os.environ["OANDA_API_TOKEN"] = "test-token"
            self.assertTrue(self.bot._oanda_enabled_for_ticker_v770("XAUUSD"))
            self.assertEqual(self.bot._signal_tfs_for_asset_v765("XAUUSD"), ["5m", "15m", "30m", "45m", "1h", "4h"])
            self.assertEqual(self.bot._safe_signal_interval_v765("XAUUSD", "5m"), "5m")
            data = {
                "signal": "LONG",
                "direction": "long",
                "price": 4496.10,
                "confidence": 80,
                "prob": 0.68,
                "bull_args": ["test support"],
                "bear_args": ["test risk"],
                "risk_levels": {"entry": 4496.10, "sl": 4475.83, "tp1": 4530.42, "tp2": 4550.90, "rr_ratio": 1.67},
                "entry_plan": {"status": "ENTER_NOW", "entry_now_score": 78, "setup_score": 80, "rr_now": 1.67},
            }
            text = self.bot.format_signal_summary(data, "XAUUSD", "15m")
        finally:
            if old_token is None:
                os.environ.pop("OANDA_API_TOKEN", None)
            else:
                os.environ["OANDA_API_TOKEN"] = old_token

        self.assertIn("OANDA v20", text)
        self.assertIn("XAU_USD", text)
        self.assertNotIn("Yahoo futures proxy", text)

    def test_oanda_ohlcv_parses_candles_without_real_network(self) -> None:
        old_token = os.environ.get("OANDA_API_TOKEN")
        old_session = self.bot._session

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                candles = []
                for idx in range(80):
                    value = 4400.0 + idx
                    candles.append({
                        "complete": True,
                        "volume": 10 + idx,
                        "mid": {
                            "o": str(value),
                            "h": str(value + 2),
                            "l": str(value - 2),
                            "c": str(value + 1),
                        },
                    })
                return {"candles": candles}

        class FakeSession:
            def __init__(self):
                self.calls = []

            def get(self, url, params=None, headers=None, timeout=None):
                self.calls.append((url, dict(params or {}), dict(headers or {}), timeout))
                return FakeResponse()

        fake = FakeSession()
        try:
            os.environ["OANDA_API_TOKEN"] = "test-token"
            self.bot._session = fake
            data = self.bot.get_ohlcv("XAUUSD", "15m")
        finally:
            self.bot._session = old_session
            if old_token is None:
                os.environ.pop("OANDA_API_TOKEN", None)
            else:
                os.environ["OANDA_API_TOKEN"] = old_token

        self.assertEqual(len(data[3]), 80)
        self.assertEqual(data[3][-1], 4480.0)
        self.assertIn("/v3/instruments/XAU_USD/candles", fake.calls[0][0])
        self.assertEqual(fake.calls[0][1]["granularity"], "M15")
        self.assertEqual(fake.calls[0][2]["Authorization"], "Bearer test-token")

    def test_delayed_yahoo_assets_use_slow_timeframes_in_auto_scan(self) -> None:
        old_force = os.environ.get("STOCK_SIGNALS_FORCE_NYSE_OPEN")
        old_commodity_force = os.environ.get("COMMODITY_SIGNALS_FORCE_OPEN")
        old_alpaca_key = os.environ.pop("ALPACA_API_KEY_ID", None)
        old_alpaca_secret = os.environ.pop("ALPACA_API_SECRET_KEY", None)
        old_oanda = os.environ.pop("OANDA_API_TOKEN", None)
        old_oanda_alt = os.environ.pop("OANDA_TOKEN", None)
        try:
            os.environ["STOCK_SIGNALS_FORCE_NYSE_OPEN"] = "1"
            os.environ["COMMODITY_SIGNALS_FORCE_OPEN"] = "1"
            pairs = self.bot._auto_signal_scan_pairs_v765()
            aapl_tfs = [tf for ticker, tf in pairs if ticker == "AAPL"]
            xau_tfs = [tf for ticker, tf in pairs if ticker == "XAUUSD"]
            btc_tfs = [tf for ticker, tf in pairs if ticker == "BTCUSDT"]
            self.assertEqual(aapl_tfs, ["30m", "45m", "1h", "4h"])
            self.assertEqual(xau_tfs, ["30m", "45m", "1h", "4h"])
            self.assertIn("5m", btc_tfs)
            self.assertIn("15m", btc_tfs)
        finally:
            if old_force is None:
                os.environ.pop("STOCK_SIGNALS_FORCE_NYSE_OPEN", None)
            else:
                os.environ["STOCK_SIGNALS_FORCE_NYSE_OPEN"] = old_force
            if old_commodity_force is None:
                os.environ.pop("COMMODITY_SIGNALS_FORCE_OPEN", None)
            else:
                os.environ["COMMODITY_SIGNALS_FORCE_OPEN"] = old_commodity_force
            if old_oanda is not None:
                os.environ["OANDA_API_TOKEN"] = old_oanda
            if old_oanda_alt is not None:
                os.environ["OANDA_TOKEN"] = old_oanda_alt
            if old_alpaca_key is not None:
                os.environ["ALPACA_API_KEY_ID"] = old_alpaca_key
            if old_alpaca_secret is not None:
                os.environ["ALPACA_API_SECRET_KEY"] = old_alpaca_secret

    def test_stock_chart_parser_supports_manual_signals(self) -> None:
        old_fetch = self.bot._stock_fetch_yahoo_chart_v764
        old_alpaca_key = os.environ.pop("ALPACA_API_KEY_ID", None)
        old_alpaca_secret = os.environ.pop("ALPACA_API_SECRET_KEY", None)
        try:
            timestamps = list(range(1, 121))
            quote = {
                "open": [100.0 + i * 0.1 for i in range(120)],
                "high": [100.5 + i * 0.1 for i in range(120)],
                "low": [99.5 + i * 0.1 for i in range(120)],
                "close": [100.2 + i * 0.1 for i in range(120)],
                "volume": [1000 + i for i in range(120)],
            }
            fake_result = {"timestamp": timestamps, "indicators": {"quote": [quote]}, "meta": {"regularMarketPrice": 112.34}}
            seen = []
            self.bot._stock_fetch_yahoo_chart_v764 = lambda ticker, interval: seen.append((ticker, interval)) or fake_result
            data = self.bot.get_ohlcv("AAPL", "5m")
            self.assertEqual(len(data), 5)
            self.assertGreaterEqual(len(data[3]), 50)
            self.assertEqual(self.bot.get_price("AAPL"), 112.34)
            self.assertIn(("AAPL", "1h"), seen)
        finally:
            self.bot._stock_fetch_yahoo_chart_v764 = old_fetch
            if old_alpaca_key is not None:
                os.environ["ALPACA_API_KEY_ID"] = old_alpaca_key
            if old_alpaca_secret is not None:
                os.environ["ALPACA_API_SECRET_KEY"] = old_alpaca_secret

    def test_alpaca_stock_source_enables_fast_timeframes_and_card_label(self) -> None:
        old_key = os.environ.get("ALPACA_API_KEY_ID")
        old_secret = os.environ.get("ALPACA_API_SECRET_KEY")
        try:
            os.environ["ALPACA_API_KEY_ID"] = "test-key"
            os.environ["ALPACA_API_SECRET_KEY"] = "test-secret"
            self.assertTrue(self.bot._alpaca_enabled_for_ticker_v771("AAPL"))
            self.assertEqual(self.bot._signal_tfs_for_asset_v765("AAPL"), ["5m", "15m", "30m", "45m", "1h", "4h"])
            self.assertEqual(self.bot._safe_signal_interval_v765("AAPL", "5m"), "5m")
            data = {
                "signal": "LONG",
                "direction": "long",
                "price": 100.0,
                "confidence": 80,
                "prob": 0.68,
                "bull_args": ["test support"],
                "bear_args": ["test risk"],
                "risk_levels": {"entry": 100.0, "sl": 98.0, "tp1": 104.0, "tp2": 106.0, "rr_ratio": 1.67},
                "entry_plan": {"status": "ENTER_NOW", "entry_now_score": 78, "setup_score": 80, "rr_now": 1.67},
            }
            text = self.bot.format_signal_summary(data, "AAPL", "5m")
        finally:
            if old_key is None:
                os.environ.pop("ALPACA_API_KEY_ID", None)
            else:
                os.environ["ALPACA_API_KEY_ID"] = old_key
            if old_secret is None:
                os.environ.pop("ALPACA_API_SECRET_KEY", None)
            else:
                os.environ["ALPACA_API_SECRET_KEY"] = old_secret

        self.assertIn("Alpaca Market Data", text)
        self.assertIn("IEX", text)
        self.assertNotIn("Yahoo delayed", text)

    def test_alpaca_ohlcv_parses_bars_without_real_network(self) -> None:
        old_key = os.environ.get("ALPACA_API_KEY_ID")
        old_secret = os.environ.get("ALPACA_API_SECRET_KEY")
        old_session = self.bot._session

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                bars = []
                for idx in range(80):
                    value = 100.0 + idx
                    bars.append({"o": value, "h": value + 1, "l": value - 1, "c": value + 0.5, "v": 1000 + idx})
                return {"bars": {"AAPL": bars}}

        class FakeSession:
            def __init__(self):
                self.calls = []

            def get(self, url, params=None, headers=None, timeout=None):
                self.calls.append((url, dict(params or {}), dict(headers or {}), timeout))
                return FakeResponse()

        fake = FakeSession()
        try:
            os.environ["ALPACA_API_KEY_ID"] = "test-key"
            os.environ["ALPACA_API_SECRET_KEY"] = "test-secret"
            self.bot._session = fake
            data = self.bot.get_ohlcv("AAPL", "15m")
        finally:
            self.bot._session = old_session
            if old_key is None:
                os.environ.pop("ALPACA_API_KEY_ID", None)
            else:
                os.environ["ALPACA_API_KEY_ID"] = old_key
            if old_secret is None:
                os.environ.pop("ALPACA_API_SECRET_KEY", None)
            else:
                os.environ["ALPACA_API_SECRET_KEY"] = old_secret

        self.assertEqual(len(data[3]), 80)
        self.assertEqual(data[3][-1], 179.5)
        self.assertIn("/v2/stocks/bars", fake.calls[0][0])
        self.assertEqual(fake.calls[0][1]["symbols"], "AAPL")
        self.assertEqual(fake.calls[0][1]["timeframe"], "15Min")
        self.assertEqual(fake.calls[0][1]["feed"], "iex")
        self.assertEqual(fake.calls[0][2]["APCA-API-KEY-ID"], "test-key")

    def test_runtime_process_scan_matches_exact_project_bot_runtime(self) -> None:
        old_rows = self.bot._runtime_python_process_rows_v756
        old_path = self.bot._runtime_bot_runtime_path_v756
        try:
            self.bot._runtime_bot_runtime_path_v756 = lambda: os.path.normcase(r"D:\Mine\Trading project\bot_runtime.py")
            self.bot._runtime_python_process_rows_v756 = lambda: [
                {
                    "ProcessId": 111,
                    "ParentProcessId": 1,
                    "CommandLine": r'D:\Mine\Trading project\.venv\Scripts\python.exe D:\Mine\Trading project\bot_runtime.py',
                },
                {
                    "ProcessId": 222,
                    "ParentProcessId": 2,
                    "CommandLine": r'C:\Python314\python.exe C:\Temp\bot_runtime.py',
                },
            ]
            processes = self.bot._runtime_bot_processes_v755()
        finally:
            self.bot._runtime_python_process_rows_v756 = old_rows
            self.bot._runtime_bot_runtime_path_v756 = old_path

        self.assertEqual([p["pid"] for p in processes], [111])

    def test_runtime_process_scan_collapses_python_launcher_wrapper(self) -> None:
        old_rows = self.bot._runtime_python_process_rows_v756
        old_path = self.bot._runtime_bot_runtime_path_v756
        try:
            self.bot._runtime_bot_runtime_path_v756 = lambda: os.path.normcase(r"D:\Mine\Trading project\bot_runtime.py")
            self.bot._runtime_python_process_rows_v756 = lambda: [
                {
                    "ProcessId": 19832,
                    "ParentProcessId": 19980,
                    "CommandLine": r'"D:\Mine\Trading project\.venv\Scripts\python.exe" "D:\Mine\Trading project\bot_runtime.py"',
                },
                {
                    "ProcessId": 16276,
                    "ParentProcessId": 19832,
                    "CommandLine": r'"C:\Users\12345\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe" "D:\Mine\Trading project\bot_runtime.py"',
                },
            ]
            processes = self.bot._runtime_bot_processes_v755()
        finally:
            self.bot._runtime_python_process_rows_v756 = old_rows
            self.bot._runtime_bot_runtime_path_v756 = old_path

        self.assertEqual([p["pid"] for p in processes], [16276])

    def test_async_edit_message_text_uses_edit_endpoint(self) -> None:
        calls = []

        async def fake_api(session, method, payload=None):
            calls.append((method, payload or {}))
            return {"ok": True}

        old_api = self.bot.async_telegram_api
        self.bot.async_telegram_api = fake_api
        try:
            result = asyncio.run(self.bot.async_edit_message_text(
                object(),
                123,
                456,
                "<b>menu</b>",
                {"inline_keyboard": []},
            ))
        finally:
            self.bot.async_telegram_api = old_api

        self.assertTrue(result["ok"])
        self.assertEqual(calls[0][0], "editMessageText")
        self.assertEqual(calls[0][1]["chat_id"], 123)
        self.assertEqual(calls[0][1]["message_id"], 456)
        self.assertEqual(calls[0][1]["parse_mode"], "HTML")
        self.assertIn("reply_markup", calls[0][1])

    def test_testnet_status_line_distinguishes_paper_from_exchange(self) -> None:
        line = self.bot._testnet_position_status_line_v733({
            "testnet_real_order": {
                "entry": {
                    "submitted": False,
                    "ok": False,
                    "reason": "entry <blocked>",
                }
            }
        })
        self.assertIn("ордер не отправлен", line)
        self.assertIn("entry &lt;blocked&gt;", line)

    def test_testnet_only_menu_hides_paper_language(self) -> None:
        text = self.bot.format_autobot_menu(987654321)
        self.assertIn("Win Rate", text)
        self.assertIn("без ордеров", text)
        self.assertNotIn("Paper-", text)
        self.assertNotIn("paper-", text)
        self.assertNotIn("Paper Trader", text)

    def test_main_status_does_not_refresh_testnet_network_stats(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_income = self.bot._base_testnet_income_stats_v734_for_v768
        old_cache = dict(self.bot._testnet_ui_cache_v768)
        calls = {"open": 0, "income": 0}

        def fail_open():
            calls["open"] += 1
            raise AssertionError("main menu should not refresh positions")

        def fail_income(limit=1000):
            calls["income"] += 1
            raise AssertionError("main menu should not refresh income")

        try:
            self.bot._testnet_ui_cache_v768.clear()
            self.bot._testnet_open_positions_v734 = fail_open
            self.bot._base_testnet_income_stats_v734_for_v768 = fail_income
            text = self.bot.format_main_status(987654321)
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._base_testnet_income_stats_v734_for_v768 = old_income
            self.bot._testnet_ui_cache_v768.clear()
            self.bot._testnet_ui_cache_v768.update(old_cache)

        self.assertIn("Win Rate", text)
        self.assertEqual(calls, {"open": 0, "income": 0})

    def test_closed_trade_button_uses_local_lifecycle_without_rebuild(self) -> None:
        old_load = self.bot._testnet_lifecycle_load_v740
        old_plans = self.bot._execution_last_plans_v715
        old_rebuild = self.bot.rebuild_testnet_lifecycle_v740
        calls = {"rebuild": 0}

        def fail_rebuild(chat_id=None, limit=20):
            calls["rebuild"] += 1
            raise AssertionError("closed report button should not rebuild lifecycle")

        try:
            self.bot._signal_winrate_save_v777({
                "signals": [
                    {
                        "id": "s1",
                        "chat_id": "987654321",
                        "ticker": "BTCUSDT",
                        "direction": "LONG",
                        "interval": "15m",
                        "created_at": "2026-06-04T00:00:00+00:00",
                        "due_at": "2026-06-04T00:15:00+00:00",
                        "status": "WIN",
                        "entry_price": 100.0,
                        "exit_price": 101.0,
                        "result_edge_pct": 1.0,
                    }
                ]
            })
            self.bot._execution_last_plans_v715 = lambda chat_id, limit=500: [{"plan_id": "p1"}]
            self.bot.rebuild_testnet_lifecycle_v740 = fail_rebuild
            text = self.bot._simple_format_closed_positions(987654321)
        finally:
            self.bot._testnet_lifecycle_load_v740 = old_load
            self.bot._execution_last_plans_v715 = old_plans
            self.bot.rebuild_testnet_lifecycle_v740 = old_rebuild

        self.assertIn("Win Rate", text)
        self.assertIn("BTC", text)
        self.assertEqual(calls["rebuild"], 0)

    def test_testnet_gate_does_not_use_stale_paper_positions(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_count = self.bot._testnet_today_real_entry_count_v734
        old_plan = self.bot._build_testnet_trade_plan_v734
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_today_real_entry_count_v734 = lambda chat_id=None: 0
            self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: {"blockers": []}
            candidate = {
                "ticker": "BTCUSDT",
                "interval": "15m",
                "direction": "long",
                "data": {"risk_levels": {"rr_ratio": 1.67}, "risk_blockers": []},
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 88,
                    "setup_score": 88,
                    "rr_now": 1.67,
                },
            }
            self.assertIsNone(self.bot._testnet_candidate_block_reason_v735(987654321, candidate))
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_count
            self.bot._build_testnet_trade_plan_v734 = old_plan

    def test_testnet_daily_count_is_not_a_hard_trade_blocker(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_count = self.bot._testnet_today_real_entry_count_v734
        old_plan = self.bot._build_testnet_trade_plan_v734
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_today_real_entry_count_v734 = (
                lambda chat_id=None: self.bot.PAPER_TRADER_MAX_TRADES_PER_DAY
            )
            self.bot._build_testnet_trade_plan_v734 = lambda chat_id, candidate: {"blockers": []}
            candidate = {
                "ticker": "BTCUSDT",
                "interval": "15m",
                "direction": "long",
                "data": {"risk_levels": {"rr_ratio": 1.67}, "risk_blockers": []},
                "entry_plan": {
                    "status": "ENTER_NOW",
                    "entry_now_score": 88,
                    "setup_score": 88,
                    "rr_now": 1.67,
                },
            }
            self.assertIsNone(self.bot._testnet_candidate_block_reason_v735(987654321, candidate))
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_today_real_entry_count_v734 = old_count
            self.bot._build_testnet_trade_plan_v734 = old_plan

    def test_riskier_testnet_probe_candidate_is_added(self) -> None:
        data = {
            "direction": "long",
            "confidence": 48,
            "risk_levels": {"rr_ratio": 1.35},
            "risk_warnings": ["weak volume"],
            "risk_blockers": [],
            "entry_plan": {
                "status": "ENTER_NOW",
                "entry_now_score": 58,
                "setup_score": 58,
                "rr_now": 1.35,
            },
        }

        rows = self.bot._paper_strategy_candidates("probe-chat", "BTCUSDT", "15m", data)

        self.assertIn("testnet_probe_v1", {row.get("strategy") for row in rows})

    def test_strategy_learning_blocks_after_five_real_losses(self) -> None:
        old_base = self.bot._base_testnet_candidate_block_reason_v772_for_v773
        old_closed = self.bot._testnet_closed_trade_rows_v742
        try:
            self.bot._base_testnet_candidate_block_reason_v772_for_v773 = lambda *args, **kwargs: None
            self.bot._testnet_closed_trade_rows_v742 = lambda chat_id=None, limit=200: [
                {"strategy": "testnet_probe_v1", "pnl": {"status": "ATTRIBUTED", "realized_usdt": -0.01}}
                for _ in range(5)
            ]
            reason = self.bot._testnet_candidate_block_reason_v735(
                987654321,
                {"strategy": "testnet_probe_v1"},
            )
        finally:
            self.bot._base_testnet_candidate_block_reason_v772_for_v773 = old_base
            self.bot._testnet_closed_trade_rows_v742 = old_closed

        self.assertIn("strategy learning pause", reason)

    def test_strategy_learning_ignores_execution_emergency_rows(self) -> None:
        old_base = self.bot._base_testnet_candidate_block_reason_v772_for_v773
        old_closed = self.bot._testnet_closed_trade_rows_v742
        try:
            self.bot._base_testnet_candidate_block_reason_v772_for_v773 = lambda *args, **kwargs: None
            self.bot._testnet_closed_trade_rows_v742 = lambda chat_id=None, limit=200: [
                {"strategy": "testnet_probe_v1", "status": "EMERGENCY_CLOSED", "pnl": {"status": "PENDING"}}
                for _ in range(8)
            ]
            reason = self.bot._testnet_candidate_block_reason_v735(
                987654321,
                {"strategy": "testnet_probe_v1"},
            )
        finally:
            self.bot._base_testnet_candidate_block_reason_v772_for_v773 = old_base
            self.bot._testnet_closed_trade_rows_v742 = old_closed

        self.assertIsNone(reason)

    def test_demo_analytics_store_details_not_user_card(self) -> None:
        row = {
            "ticker": "BTCUSDT",
            "tf": "15m",
            "status": "ENTER_NOW",
            "entry_now": 88,
            "setup": 88,
            "rr": 1.67,
            "testnet_gate": "подробная техническая причина для локального анализа",
        }
        visible = "\n".join(self.bot._format_scan_rows([row]))
        self.assertIn("Entry: 88/100", visible)
        self.assertNotIn("подробная техническая причина", visible)

        old_file = self.bot.DEMO_ANALYTICS_STATE_FILE
        with tempfile.TemporaryDirectory() as tmp:
            self.bot.DEMO_ANALYTICS_STATE_FILE = os.path.join(tmp, "demo_analysis_state.json")
            try:
                self.bot._demo_analysis_record_cycle_v736(
                    987654321,
                    [row],
                    decision={"opened": False, "status": "NO_TRADE", "reason": "коротко для пользователя"},
                )
                state = self.bot._demo_analysis_load_v736()
                stored = state["cycles"][-1]
                self.assertEqual(stored["user_visible"]["reason"], "коротко для пользователя")
                self.assertIn("подробная техническая причина", stored["scan"]["top"][0]["testnet_gate"])
            finally:
                self.bot.DEMO_ANALYTICS_STATE_FILE = old_file

    def test_public_pnl_waits_for_bot_closed_trades(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_income = self.bot._testnet_income_stats_v734
        old_monitor = self.bot._recent_testnet_monitor_events_v730
        old_connection = self.bot._testnet_connection_status_v740
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_income_stats_v734 = lambda: {
                "ok": True,
                "closed": 2,
                "wins": 1,
                "losses": 1,
                "winrate": 50.0,
                "net": 12.34,
            }
            self.bot._recent_testnet_monitor_events_v730 = lambda chat_id=None, limit=6: []
            self.bot._testnet_connection_status_v740 = lambda force=False: {
                "state": "READY_TO_TRADE",
                "signed_ok": True,
                "reason": "ok",
            }
            text = self.bot.format_autobot_menu(987654321)
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_income_stats_v734 = old_income
            self.bot._recent_testnet_monitor_events_v730 = old_monitor
            self.bot._testnet_connection_status_v740 = old_connection

        self.assertIn("Win Rate", text)
        self.assertIn("Винрейт: <b>н/д</b>", text)
        self.assertNotIn("+12.340 USDT", text)

    def test_connection_line_is_explicit(self) -> None:
        old_status = self.bot._testnet_connection_status_v740
        try:
            self.bot._testnet_connection_status_v740 = lambda force=False: {
                "state": "READY_TO_TRADE",
                "signed_ok": True,
                "reason": "signed API OK, real Testnet submit ON",
            }
            self.assertIn("Binance: 🟢 <b>READY</b>", self.bot._testnet_connection_line_v740())
        finally:
            self.bot._testnet_connection_status_v740 = old_status

    def test_public_pnl_uses_attributed_bot_rows(self) -> None:
        old_open = self.bot._testnet_open_positions_v734
        old_income = self.bot._testnet_income_stats_v734
        old_closed = self.bot._testnet_closed_trade_rows_v742
        old_connection = self.bot._testnet_connection_status_v740
        try:
            self.bot._testnet_open_positions_v734 = lambda: ([], None)
            self.bot._testnet_income_stats_v734 = lambda: {"ok": True, "closed": 8, "net": 999.0, "winrate": 100.0}
            self.bot._testnet_closed_trade_rows_v742 = lambda chat_id=None, limit=200: [
                {"pnl": {"status": "ATTRIBUTED", "realized_usdt": 2.5}},
                {"pnl": {"status": "ATTRIBUTED", "realized_usdt": -1.0}},
            ]
            self.bot._testnet_connection_status_v740 = lambda force=False: {
                "state": "READY_TO_TRADE",
                "signed_ok": True,
                "reason": "ok",
            }
            self.bot._signal_winrate_save_v777({
                "signals": [
                    {
                        "id": "w1",
                        "chat_id": "987654321",
                        "ticker": "BTCUSDT",
                        "direction": "LONG",
                        "interval": "15m",
                        "created_at": "2026-06-04T00:00:00+00:00",
                        "due_at": "2026-06-04T00:15:00+00:00",
                        "status": "WIN",
                        "entry_price": 100.0,
                        "exit_price": 101.0,
                        "result_edge_pct": 1.0,
                    },
                    {
                        "id": "l1",
                        "chat_id": "987654321",
                        "ticker": "ETHUSDT",
                        "direction": "SHORT",
                        "interval": "30m",
                        "created_at": "2026-06-04T00:00:00+00:00",
                        "due_at": "2026-06-04T00:30:00+00:00",
                        "status": "LOSS",
                        "entry_price": 100.0,
                        "exit_price": 101.0,
                        "result_edge_pct": -1.0,
                    },
                ]
            })
            text = self.bot.format_autobot_menu(987654321)
        finally:
            self.bot._testnet_open_positions_v734 = old_open
            self.bot._testnet_income_stats_v734 = old_income
            self.bot._testnet_closed_trade_rows_v742 = old_closed
            self.bot._testnet_connection_status_v740 = old_connection

        self.assertIn("Винрейт: <b>50.0%</b>", text)
        self.assertIn("🟢 1 WIN | 🔴 1 LOSS | ⚪ 0 FLAT", text)
        self.assertNotIn("+999.000 USDT", text)

    def test_lifecycle_report_is_compact_and_user_facing(self) -> None:
        old_stats = self.bot._testnet_public_stats_v738
        old_rows = self.bot._testnet_lifecycle_recent_v740
        try:
            self.bot._testnet_public_stats_v738 = lambda chat_id: {
                "open": 1,
                "bot_closed": 2,
                "attributed_closed": 1,
                "bot_winrate": 100.0,
                "bot_net": 1.25,
            }
            self.bot._testnet_lifecycle_recent_v740 = lambda chat_id=None, limit=50: [
                {
                    "ticker": "BTCUSDT",
                    "direction": "long",
                    "interval": "15m",
                    "created_at": "2026-05-26T00:00:00+00:00",
                    "status": "CLOSED_WIN",
                    "pnl": {"status": "ATTRIBUTED", "outcome": "WIN", "realized_usdt": 1.25},
                },
                {
                    "ticker": "ETHUSDT",
                    "direction": "short",
                    "interval": "30m",
                    "created_at": "2026-05-26T00:15:00+00:00",
                    "status": "CLOSED_UNATTRIBUTED",
                    "monitor": {"status": "NO_POSITION"},
                    "pnl": {"status": "NO_INCOME_MATCH"},
                },
            ]
            text = self.bot.format_testnet_lifecycle_report_v744(987654321)
        finally:
            self.bot._testnet_public_stats_v738 = old_stats
            self.bot._testnet_lifecycle_recent_v740 = old_rows

        self.assertIn("Demo Trade Report", text)
        self.assertIn("Открытые: <b>1/3</b>", text)
        self.assertIn("Закрыта в плюс", text)
        self.assertIn("+1.250 USDT", text)
        self.assertIn("PnL", text)
        self.assertNotIn("CLOSED_WIN", text)
        self.assertNotIn("PNL_PENDING", text)
        self.assertNotIn("plan_id", text)
        self.assertNotIn("orderId", text)

    def test_lifecycle_report_explains_plan_only_and_rejected_rows(self) -> None:
        old_stats = self.bot._testnet_public_stats_v738
        old_rows = self.bot._testnet_lifecycle_recent_v740
        old_hint = self.bot._testnet_plan_failure_hint_v751
        try:
            self.bot._testnet_public_stats_v738 = lambda chat_id: {
                "open": 0,
                "bot_closed": 0,
                "attributed_closed": 0,
                "bot_winrate": None,
                "bot_net": 0,
            }
            self.bot._testnet_lifecycle_recent_v740 = lambda chat_id=None, limit=50: [
                {
                    "plan_id": "old-plan",
                    "ticker": "BNBUSDT",
                    "direction": "short",
                    "interval": "15m",
                    "created_at": "2026-05-18T02:15:00+00:00",
                    "status": "ENTRY_REJECTED",
                    "pnl": {"status": "UNATTRIBUTED"},
                },
                {
                    "plan_id": "new-plan",
                    "ticker": "ETHUSDT",
                    "direction": "long",
                    "interval": "5m",
                    "created_at": "2026-05-26T02:15:00+00:00",
                    "status": "PLANNED",
                    "pnl": {"status": "UNATTRIBUTED"},
                },
            ]
            self.bot._testnet_plan_failure_hint_v751 = lambda plan_id: "Precision is over the maximum defined for this asset."
            text = self.bot.format_testnet_lifecycle_report_v744(987654321)
            self.bot._testnet_lifecycle_recent_v740 = lambda chat_id=None, limit=50: [
                {
                    "plan_id": "plan-only",
                    "ticker": "ETHUSDT",
                    "direction": "long",
                    "interval": "5m",
                    "created_at": "2026-05-26T02:15:00+00:00",
                    "status": "PLANNED",
                    "pnl": {"status": "UNATTRIBUTED"},
                },
            ]
            plan_only_text = self.bot.format_testnet_lifecycle_report_v744(987654321)
        finally:
            self.bot._testnet_public_stats_v738 = old_stats
            self.bot._testnet_lifecycle_recent_v740 = old_rows
            self.bot._testnet_plan_failure_hint_v751 = old_hint

        self.assertIn("BNB", text)
        self.assertIn("Вход отклонён", text)
        self.assertIn("точности", text)
        self.assertNotIn("ENTRY_REJECTED", text)
        self.assertNotIn("Precision is over", text)
        self.assertNotIn("plan only, order not sent", text)
        self.assertNotIn("ETH", text)
        self.assertIn("План сохранён", plan_only_text)
        self.assertIn("ордер на биржу не отправлялся", plan_only_text)
        self.assertNotIn("PLAN_ONLY", plan_only_text)
        self.assertNotIn("plan only, order not sent", plan_only_text)

    def test_autobot_keyboard_uses_report_button_without_new_callback(self) -> None:
        keyboard = self.bot.autobot_keyboard(987654321)
        buttons = [
            button
            for row in keyboard.get("inline_keyboard", [])
            for button in row
        ]
        report = [button for button in buttons if button.get("callback_data") == "paper_closed_menu"]
        self.assertTrue(report)
        self.assertIn("статистик", report[0]["text"].lower())


if __name__ == "__main__":
    unittest.main()
