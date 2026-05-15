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

Setup analytics breaks the paper journal down by ticker, timeframe and
strategy, including SL-rate, TP-rate, average holding time, result in R, and
MFE/MAE where recent candles are available.

Probability calibration compares the bot's stated probabilities with realised
signal-journal outcomes, grouped by probability bucket, timeframe and direction.

Paper Trader uses a soft timeframe quality adjustment: weak timeframes receive a
score penalty, but they are not fully banned.

Paper Trader realism adds explicit slippage, 50% partial close on TP1, break-even
SL for the remaining position, max-hold exits, and stale-signal exits.

Execution Gateway v7.15 adds dry-run order plans. The bot records what it would
prepare for an entry, SL and TP, checks risk limits, and shows the plan in the
Autobot menu. It does not submit live Binance orders.

Optional safe execution mode:

```powershell
$env:BOT_EXECUTION_MODE="paper"   # paper, dry_run, testnet, or live_off
```

For a later Binance Futures Testnet step, use separate Testnet keys only:

```powershell
$env:BINANCE_FUTURES_TESTNET_API_KEY="..."
$env:BINANCE_FUTURES_TESTNET_API_SECRET="..."
```

Testnet Order Test v7.19 can validate entry orders through Binance Futures
Testnet `/fapi/v1/order/test`. This endpoint checks request parameters and
signature, but does not send the order to the matching engine.

```powershell
$env:BOT_EXECUTION_MODE="testnet"
$env:BINANCE_TESTNET_ORDER_SUBMIT="1"
```

Testnet Protection Orders v7.20 also validates protective orders:
`STOP_MARKET` for SL and `TAKE_PROFIT_MARKET` for TP1/TP2, all with
`reduceOnly=true`. It blocks bad geometry, for example LONG SL above entry or
SHORT TP above entry.

Testnet Journal/Reconciliation v7.21 adds a separate `testnet_journal.json`
runtime file and reports for planned order checks, accepted/rejected Testnet
validations, Binance rejection reasons, and plan-vs-result reconciliation.

The first real extraction helpers now live in:

- `quant_bot/execution_gateway.py`
- `quant_bot/safety.py`
- `quant_bot/analytics_reports.py`

Safety Kill Switch v7.16 adds an Autobot safety screen. It can pause new paper
entries, turn on observe-only mode, block after daily limits, and cool down
after a series of SL/loss exits.

Optional forced observe-only mode:

```powershell
$env:BOT_OBSERVE_ONLY="1"
```

Smart Opportunity Ranking v7.17 adds a best-setups report in Autobot. It ranks
candidate trades by EntryNow, setup strength, probability, RR, expected R,
confidence, warnings and timeframe quality, while still respecting Safety gate.

Period Performance Reports v7.18 add daily and weekly Paper Trader reviews:
winrate, net PnL, profit factor, average R, best/weak tickers, timeframe
breakdown, strategy breakdown, SL clusters and a simple probability check.

## Trading note

A working bot is not the same as a safe strategy. Before trading live, test on paper trading and check risk per trade, max drawdown, fees, slippage, and liquidation distance.
