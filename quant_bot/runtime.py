"""Application entrypoint for the Quant Signal Bot."""
from __future__ import annotations

from .legacy import run_async


def main() -> int:
    run_async()
    return 0
