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

The launcher starts `bot_runtime.py`, which imports the legacy `quant bot.py` and validates the active runtime before Telegram polling starts.

```powershell
cd "D:\Trading project"
.\run_bot.bat
```

## Trading note

A working bot is not the same as a safe strategy. Before trading live, test on paper trading and check risk per trade, max drawdown, fees, slippage, and liquidation distance.