[CmdletBinding()]
param(
    [string]$Source = (Join-Path $PSScriptRoot '..\..\hermes-agent'),
    [string]$Python = 'python',
    [string]$BuildRoot = 'D:\hermes-build'
)
$ErrorActionPreference = 'Stop'
$Source = (Resolve-Path -LiteralPath $Source).Path
$BuildRoot = [IO.Path]::GetFullPath($BuildRoot)
if ($BuildRoot -notmatch '^[dD]:\\') { throw 'BuildRoot must be on D:.' }
if ($BuildRoot -match '^D:\\hermesagent(?:-old)?(?:\\|$)') {
    throw 'Build output must not use the installation or backup directory.'
}
$baseline = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\baseline.json') -Raw | ConvertFrom-Json
$head = & git -C $Source rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $head -ne $baseline.commit) { throw 'Source HEAD does not match baseline.json.' }
$dirty = & git -C $Source status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Source checkout must be clean.' }
foreach ($directory in @($BuildRoot, "$BuildRoot\temp", "$BuildRoot\logs")) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}
# Process-scoped only; the native driver isolates its own toolchain and HOME.
$env:TEMP = "$BuildRoot\temp"
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:ELECTRON_CACHE = "$BuildRoot\cache\electron"
$env:ELECTRON_BUILDER_CACHE = "$BuildRoot\cache\electron-builder"
$log = Join-Path $BuildRoot ('logs\desktop-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
Write-Host "Source: $Source ($head)"
Write-Host "Native build log: $log"
& $Python -B (Join-Path $PSScriptRoot 'native_log.py') $log $Python -B (Join-Path $Source 'scripts\bundles\desktop.py') --repo $Source --commit $head --variant bundled --work "$BuildRoot\work" --cache "$BuildRoot\cache" -- --dir --publish never
if ($LASTEXITCODE -ne 0) { throw "Native build failed ($LASTEXITCODE). See $log" }
$output = Join-Path $Source 'apps\desktop\release\win-unpacked'
& $Python -B (Join-Path $PSScriptRoot 'artifact.py') $output $head
if ($LASTEXITCODE -ne 0) { throw 'Native artifact identity verification failed.' }
Write-Host "Unpacked product: $output"
