# Quant Bot Run Guide

## 1. Check environment

From PowerShell or CMD:

```powershell
cd "D:\Trading project"
.\run_bot.bat -CheckOnly
```

This checks Python, dependencies, syntax, safe import, runtime architecture, and whether `TELEGRAM_BOT_TOKEN` is set.

If you prefer direct PowerShell script execution:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Trading project\run_bot.ps1" -CheckOnly
```

## 2. Install or update dependencies

```powershell
cd "D:\Trading project"
.\run_bot.bat -Install -CheckOnly
```

## 3. Set Telegram token

Set the token only in the terminal environment. Do not paste the real token into code.

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABC..."
```

For CMD use:

```cmd
set TELEGRAM_BOT_TOKEN=123456:ABC...
```

## 4. Start the bot

The launcher starts `bot_runtime.py`. That entrypoint goes through the
`quant_bot` package facade, which imports the legacy `quant bot.py` and
validates the active runtime before Telegram polling starts.

```powershell
cd "D:\Trading project"
.\run_bot.bat
```

Optional direct package launch:

```powershell
cd "D:\Trading project"
python -m quant_bot
```

## 5. Architecture note

New code should be added to the `quant_bot/` package. The big `quant bot.py`
file is still the live legacy runtime, but it now has adapter modules around it:
market data, signals, risk, Paper Trader, backtesting, and Telegram UI.

Paper Trader stores a `setup_id` for each new paper position so repeated auto
cycles do not count one market idea as several independent trades.

The Autobot screen also has a bot quality report. It checks whether the current
paper and signal-journal data is large enough to tune the strategy, then shows
winrate, profit factor, average R, weak timeframes, and practical next steps.

## Trading note

A working bot is not the same as a safe strategy. Before trading live, test on paper trading and check risk per trade, max drawdown, fees, slippage, and liquidation distance.
