# Build CV Redactor Native GUI Executable
# This script builds a standalone .exe with native Windows GUI (tkinter)

param(
    [switch]$Clean,
    [switch]$Test
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CV REDACTOR NATIVE GUI - BUILD SCRIPT" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
    } else {
        Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
        exit 1
    }
}

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist\CVRedactor.exe") { Remove-Item -Force "dist\CVRedactor.exe" }
    Write-Host "Clean complete!" -ForegroundColor Green
    Write-Host ""
}

# Check PyInstaller
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$pyinstaller = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}
Write-Host "PyInstaller version: $pyinstaller" -ForegroundColor Green
Write-Host ""

# Create necessary directories
Write-Host "Creating output directories..." -ForegroundColor Yellow
$dirs = @("uploads", "redacted_output", "intelligence_output")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}
Write-Host ""

# Build the executable
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "BUILDING NATIVE GUI EXECUTABLE..." -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

pyinstaller build_cv_redactor_native_gui.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Red
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host "=" * 80 -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "BUILD SUCCESSFUL!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""

# Check if executable was created
$exePath = "dist\CVRedactor.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "Executable created:" -ForegroundColor Green
    Write-Host "  Location: $exePath" -ForegroundColor White
    Write-Host "  Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor White
    Write-Host ""
    
    # Create distribution package
    Write-Host "Creating distribution package..." -ForegroundColor Yellow
    
    $distDir = "dist\CVRedactor_Package"
    if (Test-Path $distDir) {
        Remove-Item -Recurse -Force $distDir
    }
    New-Item -ItemType Directory -Path $distDir | Out-Null
    
    # Copy executable
    Copy-Item "dist\CVRedactor.exe" -Destination $distDir
    
    # Copy config files
    Copy-Item -Recurse "config" -Destination "$distDir\config"
    
    # Create necessary directories
    New-Item -ItemType Directory -Path "$distDir\uploads" | Out-Null
    New-Item -ItemType Directory -Path "$distDir\redacted_output" | Out-Null
    New-Item -ItemType Directory -Path "$distDir\intelligence_output" | Out-Null
    
    # Create README
    $readme = @"
# CV Redactor - Native Windows Application

## Quick Start

1. Double-click CVRedactor.exe
2. Click "Browse CV..." to select your CV (PDF or DOCX)
3. Click "Save As..." to choose output location (optional - auto-suggested)
4. Click "🚀 Redact This CV"
5. Wait for processing (1-2 seconds)
6. Open the redacted output file

## Features

✅ Native Windows GUI (no browser needed)
✅ Multi-column CV support
✅ Automatic PII redaction (names, emails, phones, addresses)
✅ Fast processing (1-2 seconds per CV)
✅ Supports PDF and DOCX formats
✅ Section-wise redaction in proper sequence
✅ Real-time processing log
✅ No internet connection required

## System Requirements

- Windows 10 or later
- 4GB RAM minimum
- 500MB free disk space
- No Python installation required

## How to Use

### Step 1: Select CV
Click "Browse CV..." and select your CV file (PDF or DOCX)

### Step 2: Choose Output Location
Click "Save As..." to choose where to save the redacted CV
(Auto-suggested as: OriginalName_REDACTED.txt)

### Step 3: Redact
Click "🚀 Redact This CV" button

### Step 4: Review
Check the processing log for details
Open the output file when prompted

## Folders

- uploads/ - Temporary storage (can be deleted)
- redacted_output/ - Default output location
- intelligence_output/ - Optional intelligence outputs
- config/ - Configuration files

## Configuration

Edit files in config/ folder to customize:
- pii_patterns.json - PII detection patterns
- protected_terms.json - Terms to preserve
- locations.json - Location data
- sections.json - Section detection rules

## Troubleshooting

### Application won't start
- Run as administrator
- Check Windows Firewall
- Ensure config/ folder exists

### Slow first run
- First run: 10-15 seconds (model loading)
- Subsequent runs: 1-2 seconds

### Empty sections in output
- Normal if CV doesn't have those sections
- Check original CV to verify

## Privacy & Security

✅ All processing happens locally
✅ No data sent to external servers
✅ No internet connection required
✅ Files stored only in local folders

## Version

Built: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Type: Native Windows GUI (tkinter)
Success Rate: 85.3% (tested on 68 CVs)
"@
    
    Set-Content -Path "$distDir\README.txt" -Value $readme
    
    Write-Host "Distribution package created:" -ForegroundColor Green
    Write-Host "  Location: $distDir" -ForegroundColor White
    Write-Host ""
    
    # Create ZIP archive
    Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
    $zipPath = "dist\CVRedactor_Package.zip"
    if (Test-Path $zipPath) {
        Remove-Item -Force $zipPath
    }
    
    Compress-Archive -Path "$distDir\*" -DestinationPath $zipPath
    
    if (Test-Path $zipPath) {
        $zipSize = (Get-Item $zipPath).Length / 1MB
        Write-Host "ZIP archive created:" -ForegroundColor Green
        Write-Host "  Location: $zipPath" -ForegroundColor White
        Write-Host "  Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "READY FOR DISTRIBUTION!" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Distribution files:" -ForegroundColor Yellow
    Write-Host "  1. Native GUI executable: dist\CVRedactor.exe" -ForegroundColor White
    Write-Host "  2. Complete package: $distDir" -ForegroundColor White
    Write-Host "  3. ZIP archive: $zipPath" -ForegroundColor White
    Write-Host ""
    
    # Test if requested
    if ($Test) {
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host "TESTING EXECUTABLE..." -ForegroundColor Yellow
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Starting CVRedactor.exe..." -ForegroundColor Yellow
        Write-Host "The native GUI window should open." -ForegroundColor Gray
        Write-Host ""
        
        & $exePath
    } else {
        Write-Host "To test the executable, run:" -ForegroundColor Yellow
        Write-Host "  .\dist\CVRedactor.exe" -ForegroundColor White
        Write-Host ""
        Write-Host "Or run this script with -Test flag:" -ForegroundColor Yellow
        Write-Host "  .\build_native_gui.ps1 -Test" -ForegroundColor White
    }
} else {
    Write-Host "ERROR: Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
