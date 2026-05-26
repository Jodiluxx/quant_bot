@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_bot.ps1" %*
exit /b %ERRORLEVEL%
