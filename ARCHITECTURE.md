# Runtime Architecture

The project now has two levels:

1. `quant_bot/` is the clean package facade. New code should import through
   this package.
2. `quant bot.py` is the legacy runtime. It still contains the current trading
   logic and Telegram bot behavior.

This is intentional. The bot already works, so the safe migration path is:

1. Add stable module boundaries.
2. Keep behavior unchanged.
3. Move real implementations out of `quant bot.py` one area at a time.
4. Run setup checks after every move.

## Package map

```text
quant_bot/
  __main__.py              python -m quant_bot entrypoint
  runtime.py               application entrypoint
  legacy.py                only module that imports quant bot.py
  paths.py                 project paths
  config.py                safe config helpers
  adapters/
    market_data.py         candles, price, futures context
    signals.py             signal engine and message formatting
    risk.py                entry plan and risk manager
    paper.py               Paper Trader and journal report
    analytics.py           bot quality and performance diagnostics
    backtesting.py         backtest and walk-forward optimization
    telegram_app.py        Telegram UI, keyboards and async handlers
```

## Legacy layer order

`quant bot.py` is still a layered file. Several functions are intentionally
redefined: each later layer wraps the previous active function and then becomes
the new active runtime function.

Current active runtime is `v7.19 Testnet Order Test`.

Layer summary:

1. base: core indicators, signal voting, sync Telegram fallback
2. v5.6-v5.9: journal, SQLite, async runtime, organized UI and learning menus
3. v6.0-v6.5: entry timing, scheduler, futures context, backtest, WFO, risk gate
4. v6.6-v6.9: compact cards, signal submenu, futures aliases, backtest tuning
5. v7.0-v7.4: Paper Trader, all-asset scanner, Autobot menu, responsiveness
6. v7.5-v7.8.4: reliable reports, clean journal, autostart tasks, sorted Autobot
7. v7.9: Paper Trader setup IDs, duplicate guard, independent setup statistics
8. v7.10: bot quality report, profit factor, average R, signal diagnostics
9. v7.11: setup analytics by ticker, timeframe, strategy, hold time, MFE/MAE
10. v7.12: probability calibration by forecast bucket, timeframe and direction
11. v7.13: soft Paper Trader timeframe weighting from calibrated signal stats
12. v7.14: Paper Trader slippage, partial TP1, break-even SL and max-hold exits
13. v7.15: dry-run execution gateway with order plans and live trading blocked
14. v7.16: safety kill switch, observe-only mode and SL-series cooldown
15. v7.17: smart opportunity ranking and best-setups report
16. v7.18: daily and weekly Paper Trader performance reports
17. v7.19: Binance Futures Testnet `/fapi/v1/order/test` validation

The active functions are registered in `ACTIVE_RUNTIME_FUNCTIONS` near the
bottom of `quant bot.py`.

Use this to check the architecture without starting the bot:

```powershell
cd "D:\Trading project"
.\run_bot.bat -CheckOnly
```

Use this to start the bot:

```powershell
cd "D:\Trading project"
.\run_bot.bat
```

Optional direct package launch:

```powershell
cd "D:\Trading project"
python -m quant_bot
```

Do not delete earlier duplicate-looking functions until their wrapper chain has
been folded into the final active implementation. Some older definitions are
still used through `_base_*` references.
