from __future__ import annotations

import time
import unittest

from quant_bot.legacy import load_bot_module


class RuntimeMaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bot = load_bot_module(reload=True)

    def test_prune_runtime_caches_removes_stale_entries(self) -> None:
        old_ohlcv = dict(self.bot._ohlcv_cache)
        old_price = dict(self.bot._price_cache_v74)
        old_analysis = dict(self.bot._analysis_cache_v74)
        old_scan = dict(self.bot._scan_analysis_cache_v74)
        old_last_prune = self.bot._runtime_cache_last_prune_v761
        now_ts = time.time()
        stale_ts = now_ts - self.bot.RUNTIME_CACHE_MAX_AGE_SEC_V761 - 60
        try:
            self.bot._ohlcv_cache.clear()
            self.bot._price_cache_v74.clear()
            self.bot._analysis_cache_v74.clear()
            self.bot._scan_analysis_cache_v74.clear()
            self.bot._ohlcv_cache[("BTCUSDT", "15m")] = {"ts": stale_ts, "data": "old"}
            self.bot._ohlcv_cache[("ETHUSDT", "15m")] = {"ts": now_ts, "data": "fresh"}
            self.bot._price_cache_v74["BTCUSDT"] = {"ts": stale_ts, "data": 1.0}
            self.bot._analysis_cache_v74[("SOLUSDT", "1h")] = {"ts": stale_ts, "data": {}}
            self.bot._scan_analysis_cache_v74[("XRPUSDT", "30m")] = {"ts": now_ts, "data": {}}

            result = self.bot.prune_runtime_caches_v761(force=True)
            fresh_ohlcv_kept = ("ETHUSDT", "15m") in self.bot._ohlcv_cache
            fresh_scan_kept = ("XRPUSDT", "30m") in self.bot._scan_analysis_cache_v74
        finally:
            self.bot._ohlcv_cache.clear()
            self.bot._ohlcv_cache.update(old_ohlcv)
            self.bot._price_cache_v74.clear()
            self.bot._price_cache_v74.update(old_price)
            self.bot._analysis_cache_v74.clear()
            self.bot._analysis_cache_v74.update(old_analysis)
            self.bot._scan_analysis_cache_v74.clear()
            self.bot._scan_analysis_cache_v74.update(old_scan)
            self.bot._runtime_cache_last_prune_v761 = old_last_prune

        self.assertFalse(result["skipped"])
        self.assertGreaterEqual(result["removed"]["ohlcv"], 1)
        self.assertGreaterEqual(result["removed"]["price"], 1)
        self.assertGreaterEqual(result["removed"]["analysis"], 1)
        self.assertTrue(fresh_ohlcv_kept)
        self.assertTrue(fresh_scan_kept)

    def test_fear_greed_uses_shared_session_and_status_validation(self) -> None:
        class FakeResponse:
            def __init__(self) -> None:
                self.raise_called = False

            def raise_for_status(self) -> None:
                self.raise_called = True

            def json(self):
                return {
                    "data": [
                        {"value": "34", "value_classification": "Fear", "timestamp": "1710000000"},
                        {"value": "38", "value_classification": "Fear", "timestamp": "1709913600"},
                    ]
                }

        class FakeSession:
            def __init__(self, response) -> None:
                self.response = response
                self.calls = []

            def get(self, url, timeout=None):
                self.calls.append((url, timeout))
                return self.response

        old_session = self.bot._session
        old_cache = dict(self.bot._fear_greed_cache)
        response = FakeResponse()
        fake_session = FakeSession(response)
        try:
            self.bot._session = fake_session
            self.bot._fear_greed_cache = {"value": None, "label": None, "ts": 0, "history": []}

            value, label, history = self.bot.get_fear_greed()
            second = self.bot.get_fear_greed()
        finally:
            self.bot._session = old_session
            self.bot._fear_greed_cache = old_cache

        self.assertEqual(value, 34)
        self.assertEqual(label, "Fear")
        self.assertEqual(len(history), 1)
        self.assertTrue(response.raise_called)
        self.assertEqual(len(fake_session.calls), 1)
        self.assertEqual(second[0], 34)


if __name__ == "__main__":
    unittest.main()
