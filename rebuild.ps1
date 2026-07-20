# rebuild.ps1 — quick dev rebuild of the C++ engine into chess_engine_cpp.pyd
# Usage:  powershell -ExecutionPolicy Bypass -File rebuild.ps1
# Skips PyInstaller; just produces the importable .pyd for local testing.

$ErrorActionPreference = "Stop"

# Locate the MinGW-w64 g++ (WinLibs UCRT build).
$candidates = @(
    "C:\Users\amogh\Downloads\winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3\mingw64\bin",
    "C:\mingw64\bin"
)
$mingw = $candidates | Where-Object { Test-Path (Join-Path $_ "g++.exe") } | Select-Object -First 1
if (-not $mingw) {
    if (Get-Command g++ -ErrorAction SilentlyContinue) { $mingw = "" }
    else { throw "g++.exe not found. Edit the candidate paths in rebuild.ps1." }
}
if ($mingw) { $env:Path = "$mingw;$env:Path" }

$inc    = python -m pybind11 --includes
$pyinc  = python -c "import sysconfig; print(sysconfig.get_path('include'))"
$pybase = python -c "import sysconfig; print(sysconfig.get_config_var('installed_base'))"

Set-Location $PSScriptRoot
$cmd = "g++ -O3 -Wall -shared -std=c++17 -static -static-libgcc -static-libstdc++ " +
       "$inc -I`"$pyinc`" bitboard.cpp chess_engine.cpp " +
       "-L`"$pybase\libs`" -lpython312 -o chess_engine_cpp.pyd"
Write-Host ">>> $cmd"
Invoke-Expression $cmd
if ($LASTEXITCODE -ne 0) { throw "Compilation failed (exit $LASTEXITCODE)" }

python -c "import chess_engine_cpp; print('OK: chess_engine_cpp imports')"
if ($LASTEXITCODE -ne 0) { throw "Import test failed" }
Write-Host "Build succeeded: chess_engine_cpp.pyd"
