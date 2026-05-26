param(
    [switch]$Install,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot
$SecretsFile = Join-Path $ProjectRoot "secrets.local.ps1"
if (Test-Path $SecretsFile) {
    . $SecretsFile
}
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$CheckScript = Join-Path $ProjectRoot "check_setup.py"
$BotFile = Join-Path $ProjectRoot "bot_runtime.py"

Write-Host "Quant Bot launcher" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"

if (-not (Test-Path $Python)) {
    Write-Host "[FAIL] Python was not found in .venv." -ForegroundColor Red
    Write-Host "Create a virtual environment first, then install requirements."
    exit 1
}

if ($Install) {
    Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
    & $Python -m pip install -r $Requirements
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& $Python $CheckScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($CheckOnly) {
    Write-Host "CheckOnly mode: bot was not started." -ForegroundColor Yellow
    exit 0
}

if ([string]::IsNullOrWhiteSpace($env:TELEGRAM_BOT_TOKEN)) {
    Write-Host "[FAIL] TELEGRAM_BOT_TOKEN is not set." -ForegroundColor Red
    Write-Host 'Set it in this PowerShell window first:'
    Write-Host '  $env:TELEGRAM_BOT_TOKEN="123456:ABC..."'
    exit 1
}

$BotRuntimePattern = [Regex]::Escape($BotFile)
$ExistingBots = @(
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match 'python' -and
            $_.CommandLine -and
            ($_.CommandLine -match $BotRuntimePattern)
        }
)
if ($ExistingBots.Count -gt 0) {
    Write-Host "[FAIL] Quant Bot is already running." -ForegroundColor Red
    Write-Host "Stop the existing bot process before starting another one:"
    foreach ($Process in $ExistingBots) {
        Write-Host ("  PID {0}: {1}" -f $Process.ProcessId, $Process.CommandLine)
    }
    Write-Host 'PowerShell stop command:'
    Write-Host '  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "bot_runtime.py" } | ForEach-Object { Stop-Process -Id $_.ProcessId }'
    exit 1
}

Write-Host "Starting bot..." -ForegroundColor Green
& $Python $BotFile
exit $LASTEXITCODE
