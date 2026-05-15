"""Configuration helpers.

Keep secrets in environment variables or ignored local files. This module only
contains safe helpers and defaults that are fine to commit.
"""
from __future__ import annotations

import os

TELEGRAM_BOT_TOKEN_ENV = "TELEGRAM_BOT_TOKEN"


def telegram_token_is_set() -> bool:
    return bool(os.getenv(TELEGRAM_BOT_TOKEN_ENV, "").strip())
