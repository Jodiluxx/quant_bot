# Local secrets for Quant Bot.
# Copy this file to secrets.local.ps1 and put your real token there.
# Do not send secrets.local.ps1 to anyone.

$env:TELEGRAM_BOT_TOKEN="PASTE_YOUR_NEW_TELEGRAM_BOT_TOKEN_HERE"

# Binance Futures Testnet only. Never put mainnet keys here for this bot stage.
# $env:BOT_EXECUTION_MODE="testnet"
# $env:BINANCE_FUTURES_TESTNET_API_KEY="PASTE_TESTNET_KEY_HERE"
# $env:BINANCE_FUTURES_TESTNET_API_SECRET="PASTE_TESTNET_SECRET_HERE"
# $env:BINANCE_TESTNET_ORDER_SUBMIT="1"
# $env:BINANCE_TESTNET_REAL_ORDER_SUBMIT="1"

# Optional market data sources for non-crypto signals.
# OANDA is used for commodities/metals when configured.
# $env:OANDA_API_TOKEN="PASTE_OANDA_TOKEN_HERE"
# $env:OANDA_ENV="practice"

# Alpaca is used for US stocks when configured.
# Basic/free equities feed is IEX, not full SIP market coverage.
# $env:ALPACA_API_KEY_ID="PASTE_ALPACA_KEY_HERE"
# $env:ALPACA_API_SECRET_KEY="PASTE_ALPACA_SECRET_HERE"
# $env:ALPACA_STOCK_FEED="iex"
