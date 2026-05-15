"""
Environment check for quant bot.py.
This script verifies dependencies, Telegram token presence, syntax, and safe import.
It does not start the bot and does not print secrets.
"""
from __future__ import annotations

import importlib.util
import os
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOT_FILE = ROOT / "quant bot.py"
RUNTIME_FILE = ROOT / "bot_runtime.py"
REQUIRED_MODULES = ["requests", "numpy", "scipy", "aiohttp", "asyncpg"]


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def main() -> int:
    errors = 0
    print("Quant Bot setup check")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Project: {ROOT}")

    if sys.version_info < (3, 10):
        fail("Python 3.10+ is required")
        errors += 1
    else:
        ok("Python version is supported")

    for module in REQUIRED_MODULES:
        if importlib.util.find_spec(module) is None:
            fail(f"Missing dependency: {module}")
            errors += 1
        else:
            ok(f"Dependency installed: {module}")

    if not BOT_FILE.exists():
        fail(f"Bot file not found: {BOT_FILE}")
        return 1

    try:
        py_compile.compile(str(BOT_FILE), doraise=True)
        ok("quant bot.py syntax compiles")
        if RUNTIME_FILE.exists():
            py_compile.compile(str(RUNTIME_FILE), doraise=True)
            ok("bot_runtime.py syntax compiles")
        else:
            warn("bot_runtime.py is missing; direct legacy launch is still possible")
    except Exception as exc:
        fail(f"Syntax/import compile error: {exc}")
        return 1

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        ok("TELEGRAM_BOT_TOKEN is set")
    else:
        warn("TELEGRAM_BOT_TOKEN is not set; the bot will not start until you set it")

    try:
        spec = importlib.util.spec_from_file_location("quant_bot_import_check", BOT_FILE)
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not create module spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ok("quant bot.py imports without starting the bot")
        if hasattr(module, "validate_runtime_architecture"):
            module.validate_runtime_architecture()
            ok("Runtime architecture validates")
        if hasattr(module, "runtime_architecture_report"):
            print(module.runtime_architecture_report())
        else:
            print(f"Active full_analyze line: {module.full_analyze.__code__.co_firstlineno}")
            print(f"Active get_ohlcv line: {module.get_ohlcv.__code__.co_firstlineno}")
            print(f"Active async_handle_update line: {module.async_handle_update.__code__.co_firstlineno}")
    except Exception as exc:
        fail(f"Safe import failed: {exc}")
        errors += 1

    if errors:
        fail(f"Setup check finished with {errors} problem(s)")
        return 1
    ok("Setup check finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())