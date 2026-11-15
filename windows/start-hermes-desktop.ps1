$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\hermes-env.ps1"
Set-Location 'D:\hermesagent\workspace'
$desktopExe = 'D:\hermesagent\app\apps\desktop\release\win-unpacked\Hermes.exe'
if ($args.Count -eq 0 -and (Test-Path -LiteralPath $desktopExe)) {
    $env:HERMES_DESKTOP_HERMES_ROOT = 'D:\hermesagent\app'
    $env:HERMES_DESKTOP_CWD = 'D:\hermesagent\workspace'
    Start-Process -FilePath $desktopExe -WorkingDirectory $env:HERMES_DESKTOP_CWD | Out-Null
    exit 0
}
& 'D:\hermesagent\home\bin\hermes.exe' desktop --cwd 'D:\hermesagent\workspace' @args
exit $LASTEXITCODE
