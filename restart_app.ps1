# Restart the CV Redaction App
# This script stops any running instances and starts fresh

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "RESTARTING CV REDACTION APP" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Stop any running Python processes
Write-Host "Stopping any running Python processes..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Clear Python cache
Write-Host "Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Cache cleared!" -ForegroundColor Green
Write-Host ""

# Start the app
Write-Host "Starting the app..." -ForegroundColor Yellow
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "The browser will open automatically at http://localhost:5000/redactor" -ForegroundColor Green
Write-Host "Upload your CV to test the improved extraction!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

python app_launcher.py
