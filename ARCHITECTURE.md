# Runtime Architecture

`quant bot.py` is a legacy layered file. Several functions are intentionally redefined: each later layer wraps the previous active function and then becomes the new active runtime function.

Current layer order:

1. base: indicators, signal voting, sync Telegram fallback
2. v5.6: signal journal, self-score, quality/risk blockers
3. v5.7: SQLite state, candle cache, ensemble, portfolio analytics
4. v5.8: async Telegram runtime, futures websocket, orderflow storage
5. v5.9: organized Telegram UI and learning menus
6. v6.0: entry timing / entry point engine
7. v6.1: aligned auto scheduler, per-task auto jobs, 45m support
8. v6.2: mark price, funding, open interest, futures volume context
9. v6.3: event backtest metrics, R-multiples, fees, exposure and trade log
10. v6.4: timestamped walk-forward train/test validation and MTF alignment
11. v6.5: portfolio risk gate, daily limits, leverage and liquidation checks

The active functions are registered in `ACTIVE_RUNTIME_FUNCTIONS` near the bottom of `quant bot.py`.

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

Do not delete earlier duplicate-looking functions until their wrapper chain has been folded into the final active implementation. Some older definitions are still used through `_base_*` references.