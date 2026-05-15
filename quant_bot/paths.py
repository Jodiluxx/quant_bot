"""Filesystem paths used by the bot package."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_BOT_FILE = ROOT / "quant bot.py"
LEGACY_MODULE_NAME = "quant_bot_legacy_runtime"
