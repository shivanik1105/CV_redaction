# PowerShell script to test CV redaction
# Usage: .\test_cv_redaction.ps1 <path_to_pdf>

param(
    [Parameter(Mandatory=$true)]
    [string]$PdfPath
)

if (-not (Test-Path $PdfPath)) {
    Write-Host "Error: File not found: $PdfPath" -ForegroundColor Red
    exit 1
}

Write-Host "Testing CV Redaction..." -ForegroundColor Cyan
Write-Host "Input: $PdfPath" -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
}

# Run the test
python app_launcher.py --test "$PdfPath"

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`nTest completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nTest failed!" -ForegroundColor Red
}

exit $exitCode
