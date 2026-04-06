# PowerShell build script for CV Redactor GUI executable
# This builds the GUI version with a graphical interface

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Building CV Redactor GUI Executable" -ForegroundColor Cyan
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

# Check if spaCy model is installed
Write-Host ""
Write-Host "Checking spaCy model..." -ForegroundColor Yellow
try {
    python -c "import en_core_web_sm" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing spaCy model..." -ForegroundColor Yellow
        python -m spacy download en_core_web_sm
    } else {
        Write-Host "spaCy model found" -ForegroundColor Green
    }
} catch {
    Write-Host "Installing spaCy model..." -ForegroundColor Yellow
    python -m spacy download en_core_web_sm
}

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist\CVRedactorGUI.exe") {
    Remove-Item -Recurse -Force "dist\CVRedactorGUI.exe"
    Write-Host "Removed old CVRedactorGUI.exe" -ForegroundColor Green
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Removed build/" -ForegroundColor Green
}

Write-Host ""
Write-Host "Building CV Redactor GUI executable..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

# Build using spec file
pyinstaller build_cv_redactor_gui.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Build SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "dist\CVRedactorGUI.exe") {
        $fileSize = (Get-Item "dist\CVRedactorGUI.exe").Length / 1MB
        Write-Host "Executable location: dist\CVRedactorGUI.exe" -ForegroundColor Cyan
        Write-Host "File size: $([math]::Round($fileSize, 1)) MB" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "What this .exe does:" -ForegroundColor Yellow
    Write-Host "  - Graphical user interface (GUI)" -ForegroundColor White
    Write-Host "  - Drag-and-drop folder selection" -ForegroundColor White
    Write-Host "  - Real-time processing log" -ForegroundColor White
    Write-Host "  - Progress indicator" -ForegroundColor White
    Write-Host "  - No command line needed!" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  1. Double-click CVRedactorGUI.exe" -ForegroundColor White
    Write-Host "  2. Select input folder (CVs)" -ForegroundColor White
    Write-Host "  3. Select output folder" -ForegroundColor White
    Write-Host "  4. Click 'Process CVs'" -ForegroundColor White
    Write-Host "  5. Done!" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test: .\dist\CVRedactorGUI.exe" -ForegroundColor White
    Write-Host "2. Distribute: Share dist\CVRedactorGUI.exe" -ForegroundColor White
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
