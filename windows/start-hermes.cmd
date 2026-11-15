@echo off
if not "%~1"=="" goto command
call "%~dp0start-hermes-desktop.cmd"
:command
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-hermes.ps1" %*
exit /b %errorlevel%
