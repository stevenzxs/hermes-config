param([string]$Source = (Join-Path $PSScriptRoot '..\..\hermes-agent'))
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'build-hermes.ps1'
foreach ($root in @('C:\not-allowed', 'D:\hermesagent', 'D:\hermesagent-old\build')) {
    $rejected = $false
    try { & $script -Source $source -BuildRoot $root -Python 'must-not-execute.exe' }
    catch {
        if ($_.Exception.Message -notmatch 'BuildRoot must be on D:|must not use the installation') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw "Unsafe build root was accepted: $root" }
}
Write-Output 'Build root rejection tests: PASS (3 cases)'
