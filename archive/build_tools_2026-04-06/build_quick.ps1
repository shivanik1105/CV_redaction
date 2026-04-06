# Quick build script using ONEDIR mode (faster and more reliable)
# Creates a folder with exe and supporting files

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Quick Build - CV Intelligence System" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Using ONEDIR mode (folder with exe + files)" -ForegroundColor Yellow
Write-Host "This is MUCH faster than single-exe mode!" -ForegroundColor Yellow
Write-Host ""

# Clean previous builds
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

Write-Host "Building..." -ForegroundColor Yellow
Write-Host ""

# Build using onedir spec
pyinstaller build_onedir.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Build SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "dist\CVIntelligence") {
        $folderSize = (Get-ChildItem "dist\CVIntelligence" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "Output folder: dist\CVIntelligence\" -ForegroundColor Cyan
        Write-Host "Folder size: $([math]::Round($folderSize, 1)) MB" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To run: .\dist\CVIntelligence\CVIntelligence.exe" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To distribute: Zip the entire dist\CVIntelligence folder" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Build FAILED!" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to continue"
