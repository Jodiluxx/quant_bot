"""Modular facade for the Quant Signal Bot.

The live trading logic is still in the legacy file ``quant bot.py``. This
package gives the project stable module boundaries so code can be migrated out
of the legacy file in small, testable steps.
"""
from __future__ import annotations

from .legacy import load_bot_module, runtime_report, validate_runtime_architecture

__all__ = [
    "load_bot_module",
    "runtime_report",
    "validate_runtime_architecture",
]
