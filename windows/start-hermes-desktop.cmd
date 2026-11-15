@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-hermes-desktop.ps1" %*
if not errorlevel 1 exit /b 0
echo Hermes Desktop failed to launch. See the error above.
pause
exit /b %errorlevel%
