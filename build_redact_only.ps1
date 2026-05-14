# Build script for RedactOnly.exe (redaction-only CLI)
# Usage:
#   .\build_redact_only.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Building RedactOnly.exe (redaction-only)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Ensure PyInstaller exists
Write-Host "Checking PyInstaller..." -ForegroundColor Yellow
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
if (Test-Path "dist\RedactOnly.exe") { Remove-Item -Force "dist\RedactOnly.exe" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

Write-Host "" 
Write-Host "Running PyInstaller..." -ForegroundColor Yellow
pyinstaller build_redact_only.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host "" 
    Write-Host "Build FAILED" -ForegroundColor Red
    exit 1
}

Write-Host "" 
Write-Host "Build SUCCESS" -ForegroundColor Green
if (Test-Path "dist\RedactOnly.exe") {
    $sizeMb = (Get-Item "dist\RedactOnly.exe").Length / 1MB
    Write-Host ("Output: dist\\RedactOnly.exe (" + [math]::Round($sizeMb, 1) + " MB)") -ForegroundColor Cyan
}

Write-Host "" 
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  .\dist\RedactOnly.exe <file-or-dir>" -ForegroundColor White
Write-Host "  .\dist\RedactOnly.exe <file> --stdout" -ForegroundColor White
Write-Host "  .\dist\RedactOnly.exe <dir> --json" -ForegroundColor White
