"""Clean entrypoint for the Quant Signal Bot."""
from __future__ import annotations

from quant_bot.legacy import load_bot_module
from quant_bot.runtime import main


if __name__ == "__main__":
    raise SystemExit(main())
