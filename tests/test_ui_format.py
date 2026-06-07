from __future__ import annotations

import unittest

from quant_bot.ui_format import (
    RULE,
    clamp_score,
    code,
    compact_tf,
    edge_text,
    html_escape,
    scan_status,
    score_bar,
    short_text,
    status_emoji,
    status_human,
    status_plain,
    winrate_bar,
)


class UiFormatHelperTests(unittest.TestCase):
    def test_html_escape_and_code_keep_telegram_html_safe(self) -> None:
        self.assertEqual(html_escape("BTC & ETH < SOL > XRP"), "BTC &amp; ETH &lt; SOL &gt; XRP")
        self.assertEqual(code("BTC<USDT>"), "<code>BTC&lt;USDT&gt;</code>")

    def test_short_text_collapses_whitespace_and_truncates(self) -> None:
        self.assertEqual(short_text("one\n two   three", 30), "one two three")
        self.assertEqual(short_text("abcdef", 4), "abc…")
        self.assertEqual(short_text("A&B<C>", 20), "A&amp;B&lt;C&gt;")

    def test_compact_timeframe_labels(self) -> None:
        self.assertEqual(compact_tf("5m"), "5м")
        self.assertEqual(compact_tf("1h"), "1ч")
        self.assertEqual(compact_tf("1d"), "1д")
        self.assertEqual(compact_tf("custom", "15 минут"), "15м")
        self.assertEqual(compact_tf("custom", "4 часа"), "4ч")

    def test_status_labels_are_user_facing(self) -> None:
        self.assertEqual(status_plain("ENTER_NOW"), "READY")
        self.assertEqual(status_plain("WAIT_RETEST"), "WAIT RETEST")
        self.assertEqual(status_plain("WAIT_CONFIRMATION"), "WAIT CONFIRM")
        self.assertEqual(status_plain("NO_ENTRY"), "BLOCKED")
        self.assertEqual(status_human("WAIT_RETEST"), "WAIT: ожидание ретеста")
        self.assertEqual(status_emoji("NO_ENTRY"), "🔴 BLOCKED")
        self.assertEqual(scan_status("LONG"), "🟢 LONG")
        self.assertEqual(scan_status("SHORT"), "🔴 SHORT")
        self.assertEqual(scan_status("ERROR"), "⚪ ERROR")
        self.assertEqual(scan_status("WAIT_RETEST"), "🟡 WAIT")

    def test_score_and_winrate_bars_are_bounded(self) -> None:
        self.assertEqual(clamp_score(-10), 0)
        self.assertEqual(clamp_score(120), 100)
        self.assertEqual(score_bar(100, 4), "🟩🟩🟩🟩")
        self.assertEqual(score_bar(50, 4), "🟨🟨⬜⬜")
        self.assertEqual(score_bar("bad", 4), "⬜⬜⬜⬜")
        self.assertEqual(winrate_bar(None, 4), "⬜⬜⬜⬜")
        self.assertEqual(winrate_bar(75, 4), "🟩🟩🟩⬜")

    def test_edge_text_and_rule_are_stable(self) -> None:
        self.assertEqual(RULE, "───────────────────")
        self.assertEqual(edge_text(1.234), "🟢 +1.23%")
        self.assertEqual(edge_text(-0.5), "🔴 -0.50%")
        self.assertEqual(edge_text(0), "⚪ +0.00%")
        self.assertEqual(edge_text("bad"), "⚪ н/д")


if __name__ == "__main__":
    unittest.main()
