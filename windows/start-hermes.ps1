. "$PSScriptRoot\hermes-env.ps1"
Set-Location 'D:\hermesagent\workspace'
& 'D:\hermesagent\home\bin\hermes.exe' @args
exit $LASTEXITCODE
