$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this file normally, NOT as administrator. Desktop and gateway must use the same permissions.'
}
. "$PSScriptRoot\hermes-env.ps1"
& "$PSScriptRoot\home\bin\hermes.exe" gateway restart
if ($LASTEXITCODE -ne 0) { throw 'Gateway restart failed.' }
$line = Get-Content "$PSScriptRoot\home\.env" | Where-Object { $_ -match '^API_SERVER_KEY=' } | Select-Object -Last 1
if (-not $line) { throw 'API_SERVER_KEY is missing.' }
$key = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8642/api/sessions' -Headers @{Authorization="Bearer $key"} -TimeoutSec 3
        $ready = $true
        break
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ready) { throw 'Authenticated API check failed. Check home\logs\gateway.log. Do not share secrets from .env.' }
Write-Host 'Authenticated API check passed.' -ForegroundColor Green
Write-Host 'Android Host: 192.168.3.227'
Write-Host 'Android Port: 8642'
Write-Host 'Your API key (private; enter it only in your Android app):'
Write-Host $key
Write-Host 'Do not post this key in chat or screenshots.' -ForegroundColor Yellow
