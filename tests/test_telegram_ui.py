from __future__ import annotations

import unittest

from quant_bot.telegram_ui import button, callback_values, chunked_buttons, has_callback, keyboard, nav_row, row


class TelegramUiHelperTests(unittest.TestCase):
    def test_keyboard_builds_inline_markup(self) -> None:
        markup = keyboard(
            row(button("Signal", "menu_signal")),
            row(button("Win Rate", "menu_autobot"), button("Settings", "auto_settings")),
            None,
            row(None),
        )

        self.assertEqual(markup["inline_keyboard"][0][0]["callback_data"], "menu_signal")
        self.assertEqual(callback_values(markup), ["menu_signal", "menu_autobot", "auto_settings"])

    def test_callbacks_are_stringified_and_detectable(self) -> None:
        markup = keyboard(row(button("Page", 3)))

        self.assertEqual(callback_values(markup), ["3"])
        self.assertTrue(has_callback(markup, "3"))
        self.assertFalse(has_callback(markup, "missing"))

    def test_chunked_buttons_and_nav_row_are_stable(self) -> None:
        buttons = [button(f"B{i}", f"cb{i}") for i in range(5)]
        rows = chunked_buttons(buttons, width=2)

        self.assertEqual([len(item) for item in rows], [2, 2, 1])
        markup = keyboard(*rows, nav_row("menu_signal"))
        self.assertEqual(callback_values(markup)[-2:], ["menu_signal", "back_main"])


if __name__ == "__main__":
    unittest.main()
