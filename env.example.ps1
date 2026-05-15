# Copy the line below into PowerShell and replace the value with your real Telegram bot token.
# Do not commit or share the real token.
$env:TELEGRAM_BOT_TOKEN="PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Optional: PostgreSQL storage. If empty, the bot uses SQLite fallback.
# $env:DATABASE_URL="postgresql://user:password@localhost:5432/quant_bot"

# Optional: execution gateway mode.
# Safe default is paper. Supported values: paper, dry_run, testnet, live_off.
# v7.19 builds and logs order plans; Testnet validation needs explicit flags.
$env:BOT_EXECUTION_MODE="paper"

# Optional: Binance Futures Testnet keys for a later Testnet package.
# Use separate Testnet keys only, never real mainnet keys.
# $env:BINANCE_FUTURES_TESTNET_API_KEY="PASTE_TESTNET_KEY_HERE"
# $env:BINANCE_FUTURES_TESTNET_API_SECRET="PASTE_TESTNET_SECRET_HERE"
# $env:BINANCE_TESTNET_ORDER_SUBMIT="1"  # validates entry + SL/TP via /fapi/v1/order/test

# Optional: force observe-only mode from the launcher environment.
# In observe-only mode the bot analyzes and reports, but does not open new paper trades.
# $env:BOT_OBSERVE_ONLY="1"
