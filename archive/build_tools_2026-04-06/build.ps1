# PowerShell build script for CV Intelligence System
# Run: .\build.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Building CV Intelligence System .exe" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
Write-Host "Checking PyInstaller..." -ForegroundColor Yellow
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
        pip install pyinstaller
    } else {
        Write-Host "PyInstaller found" -ForegroundColor Green
    }
} catch {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "Removed dist/" -ForegroundColor Green
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Removed build/" -ForegroundColor Green
}

Write-Host ""
Write-Host "Building executable..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

# Build using simplified spec file
pyinstaller build_simple.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Build SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "dist\CVIntelligence.exe") {
        $fileSize = (Get-Item "dist\CVIntelligence.exe").Length / 1MB
        Write-Host "Executable location: dist\CVIntelligence.exe" -ForegroundColor Cyan
        Write-Host "File size: $([math]::Round($fileSize, 1)) MB" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test: .\dist\CVIntelligence.exe" -ForegroundColor White
    Write-Host "2. Distribute to users" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "Build FAILED!" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to continue"
