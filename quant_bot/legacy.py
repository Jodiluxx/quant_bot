"""Loader and compatibility helpers for the legacy bot runtime.

This module is the single place that knows how to import ``quant bot.py``.
Everything else should go through this facade instead of loading the file with
spaces in its name directly.
"""
from __future__ import annotations

import importlib.util
import sys
import threading
from types import ModuleType
from typing import Any, Callable

from .paths import LEGACY_BOT_FILE, LEGACY_MODULE_NAME

_module: ModuleType | None = None
_lock = threading.RLock()


def load_bot_module(*, reload: bool = False) -> ModuleType:
    """Load and cache the legacy runtime module without starting the bot."""
    global _module

    with _lock:
        if _module is not None and not reload:
            return _module

        if not LEGACY_BOT_FILE.exists():
            raise FileNotFoundError(f"Legacy bot file not found: {LEGACY_BOT_FILE}")

        if reload:
            sys.modules.pop(LEGACY_MODULE_NAME, None)
            _module = None

        spec = importlib.util.spec_from_file_location(LEGACY_MODULE_NAME, LEGACY_BOT_FILE)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load bot module from {LEGACY_BOT_FILE}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[LEGACY_MODULE_NAME] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(LEGACY_MODULE_NAME, None)
            raise

        _module = module
        return module


def get_bot_module() -> ModuleType:
    """Return the cached runtime module, loading it on first use."""
    return load_bot_module()


def require_callable(name: str) -> Callable[..., Any]:
    """Return a callable from the legacy runtime or fail with a clear error."""
    value = getattr(get_bot_module(), name, None)
    if not callable(value):
        raise AttributeError(f"Legacy runtime callable is missing: {name}")
    return value


def call_legacy(name: str, *args: Any, **kwargs: Any) -> Any:
    """Call a legacy runtime function by name."""
    return require_callable(name)(*args, **kwargs)


def validate_runtime_architecture() -> bool:
    """Run the legacy runtime self-check."""
    validate = require_callable("validate_runtime_architecture")
    return bool(validate())


def runtime_report() -> str:
    """Return the human-readable runtime architecture report."""
    report = getattr(get_bot_module(), "runtime_architecture_report", None)
    if callable(report):
        return str(report())
    return "Runtime report is not available in the legacy bot."


def run_async() -> None:
    """Start the Telegram bot runtime."""
    require_callable("run_async")()
