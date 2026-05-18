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

Real Testnet Orders v7.29 can send real Binance Futures Testnet orders through
`POST /fapi/v1/order`. This is still demo/Testnet only. It requires all of:
Testnet mode, Testnet API keys, `/order/test` validation enabled, and a
separate real-submit flag.

```powershell
$env:BOT_EXECUTION_MODE="testnet"
$env:BINANCE_TESTNET_ORDER_SUBMIT="1"
$env:BINANCE_TESTNET_REAL_ORDER_SUBMIT="1"
```

If a real Testnet entry is accepted but protective SL/TP orders fail, the bot
attempts an emergency reduce-only market close and records the event in the
Testnet journal. Mainnet/live order submission remains blocked by code.

Testnet Position Monitor v7.30 is read-only. It checks accepted real Testnet
entries against `/fapi/v2/positionRisk` and `/fapi/v1/openOrders`, then reports
whether the position exists, direction matches the plan, and reduce-only
`STOP_MARKET`/`TAKE_PROFIT_MARKET` protection is visible. It does not enable
mainnet trading and does not silently change strategy decisions.

Live Readiness Checklist v7.22 adds a go/no-go report in Autobot. It checks
whether there are enough paper trades, independent setup statistics, accepted
Testnet reconciliations, daily loss limits, position limits and kill-switch
controls. It does not enable live trading; mainnet order submission remains
blocked by code.

Paper Trader State Extraction v7.23 moves state filtering and data-quality
helpers into `quant_bot/paper_trader.py`: open positions, closed trades, daily
trade count, independent setup count and duplicate-row diagnostics. Strategy
logic remains in the legacy runtime for now.

Paper Journal + Execution View Helpers v7.24 moves another safe layer out of
the legacy runtime: Paper journal labels/factors/strategy summaries now live in
`quant_bot/paper_trader.py`, and execution/testnet display helpers live in
`quant_bot/execution_gateway.py`. These helpers format reports only; they do
not change entry rules or live-trading permissions.

Migration Checklist + Tests Foundation v7.25 adds an Autobot migration report
and a first `unittest` suite for Paper Trader state, Live Readiness,
Execution/Testnet reconciliation, migration status, protection geometry and
probability calibration.

Paper Trader Engine Extraction v7.26 moves the core paper position-management
math into `quant_bot/paper_trader.py`: worse fill prices, partial TP1,
break-even SL, max-hold timing, price exit signals and close-trade accounting.
The legacy runtime still owns state mutation, price fetching and Telegram side
effects.

Analytics Reports Extraction v7.27 moves probability-calibration math into
`quant_bot/analytics_reports.py`: probability normalization, probability
buckets, calibration stats and grouped ECE. The Telegram report text still
lives in the legacy runtime until the calculation layer has more tests.

Telegram UI Polish v7.28 keeps trading logic unchanged and only improves
presentation: compact main menu, shorter signal cards, cleaner
Autobot/PaperTrader buttons, compact market scan cards and readable position
updates. Existing `callback_data` values are preserved.

Demo journal reset v7.29 can archive and clear the local paper/testnet runtime
files (`paper_trader_state.json`, `execution_gateway_state.json`,
`testnet_journal.json`) so Testnet evaluation starts from a clean sheet.

Simple Public UI v7.31 hides internal analytics screens from Telegram users.
The bot still keeps and uses analytics/backtest/WFO/testnet data internally, but
the public interface shows only manual signals, auto-signal notification
settings, and demo trading status. The demo bot sends a 15-minute cycle report
that says whether a trade was opened or skipped, while choosing its own
timeframe.
Single-message Telegram navigation v7.32 keeps the public UI inside one Telegram
card where possible. Callback buttons are acknowledged with `answerCallbackQuery`
and visible menu/card transitions use `editMessageText` through `send_or_edit`,
so tapping Signal, Demo bot, Notifications, ticker/TF selectors or manual scan
updates the current message instead of flooding the chat. Scheduled auto reports
and true errors can still be sent as separate messages.

Honest Paper/Testnet status v7.33 makes the demo bot explicit about what
actually happened: an opened paper journal position is not shown as a Binance
Testnet exchange position unless the real Testnet entry order was accepted. If
Binance rejects `/order/test` or protective orders, the Telegram card says that
the Binance order was not sent and shows the short reason.

The first real extraction helpers now live in:

- `quant_bot/execution_gateway.py`
- `quant_bot/safety.py`
- `quant_bot/analytics_reports.py`
- `quant_bot/live_readiness.py`
- `quant_bot/migration.py`
- `quant_bot/paper_trader.py`

Safety Kill Switch v7.16 adds an Autobot safety screen. It can pause new paper
entries, turn on observe-only mode, block after daily limits, and cool down
after a series of SL/loss exits.

Optional forced observe-only mode:

```powershell
$env:BOT_OBSERVE_ONLY="1"
```

Run the unit tests without starting Telegram:

```powershell
cd "D:\Trading project"
python -m unittest discover -s tests
```

Smart Opportunity Ranking v7.17 adds a best-setups report in Autobot. It ranks
candidate trades by EntryNow, setup strength, probability, RR, expected R,
confidence, warnings and timeframe quality, while still respecting Safety gate.

Period Performance Reports v7.18 add daily and weekly Paper Trader reviews:
winrate, net PnL, profit factor, average R, best/weak tickers, timeframe
breakdown, strategy breakdown, SL clusters and a simple probability check.

## Trading note

A working bot is not the same as a safe strategy. Before trading live, test on paper trading and check risk per trade, max drawdown, fees, slippage, and liquidation distance.
