"""Clean entrypoint for the legacy `quant bot.py` module.

The trading bot still lives in `quant bot.py` for compatibility, but launchers use
this file so startup has a stable, importable entrypoint without spaces in the name.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOT_FILE = ROOT / "quant bot.py"
MODULE_NAME = "quant_bot_legacy_runtime"


def load_bot_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, BOT_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load bot module from {BOT_FILE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    bot = load_bot_module()
    bot.run_async()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())