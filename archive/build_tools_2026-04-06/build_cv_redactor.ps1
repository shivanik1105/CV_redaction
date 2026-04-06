# PowerShell build script for CV Redactor standalone executable
# This builds ONLY the redaction component (no LLM, no database, no web)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Building CV Redactor Standalone Executable" -ForegroundColor Cyan
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
if (Test-Path "dist\CVRedactor.exe") {
    Remove-Item -Recurse -Force "dist\CVRedactor.exe"
    Write-Host "Removed old CVRedactor.exe" -ForegroundColor Green
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Removed build/" -ForegroundColor Green
}

Write-Host ""
Write-Host "Building CV Redactor executable..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

# Build using spec file
pyinstaller build_cv_redactor.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Build SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "dist\CVRedactor.exe") {
        $fileSize = (Get-Item "dist\CVRedactor.exe").Length / 1MB
        Write-Host "Executable location: dist\CVRedactor.exe" -ForegroundColor Cyan
        Write-Host "File size: $([math]::Round($fileSize, 1)) MB" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "What this .exe does:" -ForegroundColor Yellow
    Write-Host "  - Redacts PII from CVs (names, emails, phones, addresses)" -ForegroundColor White
    Write-Host "  - Processes PDF and DOCX files" -ForegroundColor White
    Write-Host "  - Outputs anonymized text files" -ForegroundColor White
    Write-Host "  - NO LLM, NO database, NO web interface" -ForegroundColor White
    Write-Host "  - Pure standalone redaction tool" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Usage examples:" -ForegroundColor Yellow
    Write-Host "  .\dist\CVRedactor.exe resume\ output\" -ForegroundColor White
    Write-Host "  .\dist\CVRedactor.exe add-city 'Boston'" -ForegroundColor White
    Write-Host "  .\dist\CVRedactor.exe list-config" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test: .\dist\CVRedactor.exe --help" -ForegroundColor White
    Write-Host "2. Process CVs: .\dist\CVRedactor.exe resume\ output\" -ForegroundColor White
    Write-Host "3. Distribute: Share dist\CVRedactor.exe" -ForegroundColor White
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
