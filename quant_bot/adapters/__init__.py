"""Adapter modules for the current legacy runtime.

Each adapter exposes one business area. Today these functions delegate to
``quant bot.py``; later we can move real implementations behind the same names.
"""
from __future__ import annotations

__all__ = [
    "analytics",
    "backtesting",
    "execution",
    "market_data",
    "paper",
    "risk",
    "safety",
    "signals",
    "telegram_app",
]
