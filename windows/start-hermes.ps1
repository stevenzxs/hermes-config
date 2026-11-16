. "$PSScriptRoot\hermes-env.ps1"
Set-Location 'D:\hermesagent\workspace'
$stamp = Get-Content 'D:\hermesagent\app\resources\install-stamp.json' -Raw | ConvertFrom-Json
$command = Join-Path 'D:\hermesagent\app\resources\agent-payload' $stamp.runtime.commands.hermes
if (-not (Test-Path -LiteralPath $command)) { throw 'Bundled CLI is missing.' }
& $command @args
exit $LASTEXITCODE
