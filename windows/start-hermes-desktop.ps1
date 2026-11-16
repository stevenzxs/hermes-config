$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\hermes-env.ps1"
Set-Location 'D:\hermesagent\workspace'
$desktopExe = @(Get-ChildItem -LiteralPath 'D:\hermesagent\app' -Filter '*.exe' -File)
if ($desktopExe.Count -ne 1) { throw 'Expected exactly one bundled Desktop executable.' }
$env:HERMES_DESKTOP_CWD = 'D:\hermesagent\workspace'
Start-Process -FilePath $desktopExe[0].FullName -WorkingDirectory $env:HERMES_DESKTOP_CWD -ArgumentList (@($args) + '--enable-logging=file') | Out-Null
