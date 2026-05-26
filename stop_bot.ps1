param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BotFile = Join-Path $ProjectRoot "bot_runtime.py"
$BotRuntimePattern = [Regex]::Escape($BotFile)

$Processes = @(
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match 'python' -and
            $_.CommandLine -and
            ($_.CommandLine -match $BotRuntimePattern)
        }
)

if ($Processes.Count -eq 0) {
    if (-not $Quiet) {
        Write-Host "Quant Bot is not running." -ForegroundColor Yellow
    }
    exit 0
}

foreach ($Process in $Processes) {
    if (-not $Quiet) {
        Write-Host ("Stopping Quant Bot PID {0}" -f $Process.ProcessId) -ForegroundColor Yellow
    }
    Stop-Process -Id $Process.ProcessId -ErrorAction Stop
}

if (-not $Quiet) {
    Write-Host "Quant Bot stopped." -ForegroundColor Green
}
