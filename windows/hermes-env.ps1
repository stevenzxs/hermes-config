$root = 'D:\hermesagent'
$paths = @{
    HERMES_HOME = "$root\home"
    HERMES_RUNTIME_DIR = "$root\tools"
    HERMES_DESKTOP_USER_DATA_DIR = "$root\home\desktop"
    ELECTRON_CACHE = "$root\cache\electron"
    ELECTRON_BUILDER_CACHE = "$root\cache\electron-builder"
    UV_CACHE_DIR = "$root\cache\uv"
    UV_PYTHON_INSTALL_DIR = "$root\tools\uv-python"
    PIP_CACHE_DIR = "$root\cache\pip"
    npm_config_cache = "$root\cache\npm"
    HF_HOME = "$root\cache\huggingface"
    PLAYWRIGHT_BROWSERS_PATH = "$root\cache\playwright"
    TEMP = "$root\temp"
    TMP = "$root\temp"
}
foreach ($entry in $paths.GetEnumerator()) {
    New-Item -ItemType Directory -Force -Path $entry.Value | Out-Null
    Set-Item -Path "Env:$($entry.Key)" -Value $entry.Value
}
New-Item -ItemType Directory -Force -Path "$root\workspace" | Out-Null
$env:Path = "$root\home\bin;$env:Path"
