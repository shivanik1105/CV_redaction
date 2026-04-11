# Build CV Redactor GUI Executable
# This script builds a standalone .exe for the CV Redaction system

param(
    [switch]$Clean,
    [switch]$Test
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CV REDACTOR GUI - BUILD SCRIPT" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
    } else {
        Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
        Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
        Write-Host "  python -m venv .venv" -ForegroundColor White
        Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "  pip install -r requirements.txt" -ForegroundColor White
        exit 1
    }
}

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "*.spec") { 
        Get-ChildItem -Filter "*.spec" | Where-Object { $_.Name -ne "build_cv_redactor_gui.spec" } | Remove-Item -Force
    }
    Write-Host "Clean complete!" -ForegroundColor Green
    Write-Host ""
}

# Check if PyInstaller is installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$pyinstaller = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyInstaller!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "PyInstaller version: $pyinstaller" -ForegroundColor Green
Write-Host ""

# Check required packages
Write-Host "Verifying required packages..." -ForegroundColor Yellow
$required = @(
    "flask",
    "pdfplumber",
    "PyMuPDF",
    "python-docx",
    "presidio-analyzer",
    "presidio-anonymizer",
    "spacy"
)

$missing = @()
foreach ($pkg in $required) {
    $check = python -c "import $($pkg.Replace('-', '_'))" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missing += $pkg
    }
}

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing required packages:" -ForegroundColor Red
    foreach ($pkg in $missing) {
        Write-Host "  - $pkg" -ForegroundColor Red
    }
    Write-Host "`nInstall missing packages with:" -ForegroundColor Yellow
    Write-Host "  pip install $($missing -join ' ')" -ForegroundColor White
    exit 1
}

Write-Host "All required packages found!" -ForegroundColor Green
Write-Host ""

# Create necessary directories
Write-Host "Creating output directories..." -ForegroundColor Yellow
$dirs = @("uploads", "redacted_output", "intelligence_output")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "  Created: $dir/" -ForegroundColor Gray
    }
}
Write-Host ""

# Build the executable
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "BUILDING EXECUTABLE..." -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

pyinstaller build_cv_redactor_gui.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Red
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host "=" * 80 -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""

# Check if executable was created
$exePath = "dist\CVRedactorGUI.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "Executable created:" -ForegroundColor Green
    Write-Host "  Location: $exePath" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor White
    Write-Host ""
    
    # Test the executable if requested
    if ($Test) {
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host "TESTING EXECUTABLE..." -ForegroundColor Yellow
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Starting CVRedactorGUI.exe..." -ForegroundColor Yellow
        Write-Host "The application should open in your browser." -ForegroundColor Gray
        Write-Host "Press Ctrl+C to stop the test." -ForegroundColor Gray
        Write-Host ""
        
        & $exePath
    } else {
        Write-Host "To test the executable, run:" -ForegroundColor Yellow
        Write-Host "  .\dist\CVRedactorGUI.exe" -ForegroundColor White
        Write-Host ""
        Write-Host "Or run this script with -Test flag:" -ForegroundColor Yellow
        Write-Host "  .\build_exe.ps1 -Test" -ForegroundColor White
    }
} else {
    Write-Host "ERROR: Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Create distribution package
Write-Host "Creating distribution package..." -ForegroundColor Yellow

$distDir = "dist\CVRedactorGUI_Package"
if (Test-Path $distDir) {
    Remove-Item -Recurse -Force $distDir
}
New-Item -ItemType Directory -Path $distDir | Out-Null

# Copy executable
Copy-Item "dist\CVRedactorGUI.exe" -Destination $distDir

# Copy config files
Copy-Item -Recurse "config" -Destination "$distDir\config"

# Create necessary directories
New-Item -ItemType Directory -Path "$distDir\uploads" | Out-Null
New-Item -ItemType Directory -Path "$distDir\redacted_output" | Out-Null
New-Item -ItemType Directory -Path "$distDir\intelligence_output" | Out-Null

# Create README
$readme = @"
# CV Redactor GUI - Standalone Application

## Quick Start

1. Double-click CVRedactorGUI.exe
2. Your browser will open automatically
3. Upload a CV (PDF or DOCX)
4. Click "Redact CV"
5. Download the redacted output

## Features

- Multi-column CV support
- Automatic PII redaction (names, emails, phones, addresses)
- Web-based interface
- Fast processing (1-2 seconds per CV)
- Supports PDF and DOCX formats

## System Requirements

- Windows 10 or later
- 4GB RAM minimum
- 500MB free disk space

## Folders

- uploads/ - Temporary storage for uploaded files
- redacted_output/ - Redacted CV outputs
- intelligence_output/ - Optional intelligence extraction outputs
- config/ - Configuration files for redaction rules

## Configuration

Edit files in the config/ folder to customize:
- pii_patterns.json - PII detection patterns
- protected_terms.json - Terms to preserve
- locations.json - Location data
- sections.json - Section detection rules

## Troubleshooting

### Application won't start
- Check if port 5000 is available
- Run as administrator if needed
- Check Windows Firewall settings

### Browser doesn't open
- Manually navigate to: http://localhost:5000/redactor

### Slow processing
- First run takes longer (model loading)
- Subsequent runs are faster

## Support

For issues or questions, check the documentation or contact support.

## Version

Built: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Includes: Multi-column CV extraction fix
Success Rate: 85.3% (tested on 68 CVs)
"@

Set-Content -Path "$distDir\README.txt" -Value $readme

Write-Host "Distribution package created:" -ForegroundColor Green
Write-Host "  Location: $distDir" -ForegroundColor White
Write-Host ""

# Create ZIP archive
Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
$zipPath = "dist\CVRedactorGUI_Package.zip"
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path "$distDir\*" -DestinationPath $zipPath

if (Test-Path $zipPath) {
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Host "ZIP archive created:" -ForegroundColor Green
    Write-Host "  Location: $zipPath" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor White
} else {
    Write-Host "WARNING: Failed to create ZIP archive" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "READY FOR DISTRIBUTION!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Distribution files:" -ForegroundColor Yellow
Write-Host "  1. Single executable: dist\CVRedactorGUI.exe" -ForegroundColor White
Write-Host "  2. Complete package: $distDir" -ForegroundColor White
Write-Host "  3. ZIP archive: $zipPath" -ForegroundColor White
Write-Host ""
