# Restart Flask App Script
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host "RESTARTING FLASK APP"
Write-Host "=" -NoNewline; Write-Host ("=" * 79)

# Step 1: Stop existing Python processes
Write-Host "`n[1/3] Stopping existing Flask app..."
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es)"
    Write-Host "Please stop the Flask app manually (Ctrl+C in the terminal)"
    Write-Host "Then run this script again, or just run: python app.py"
    exit 1
} else {
    Write-Host "OK: No Python processes running"
}

# Step 2: Check if app.py exists
Write-Host "`n[2/3] Checking app.py..."
if (Test-Path "app.py") {
    Write-Host "OK: app.py found"
} else {
    Write-Host "ERROR: app.py not found in current directory"
    exit 1
}

# Step 3: Start the app
Write-Host "`n[3/3] Starting Flask app..."
Write-Host "Running: python app.py"
Write-Host "`nThe app will start in a new window..."
Write-Host "Watch for: 'Running on http://127.0.0.1:5000'"
Write-Host "`n" + ("=" * 80)

# Start in new window
Start-Process python -ArgumentList "app.py" -NoNewWindow

Write-Host "`nApp starting... Wait 10 seconds for initialization"
Start-Sleep -Seconds 10

# Check if it started
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "OK: Flask app is running!"
    Write-Host "`nNext steps:"
    Write-Host "1. Go to http://127.0.0.1:5000"
    Write-Host "2. Try uploading a CV"
    Write-Host "3. Check if upload works"
} else {
    Write-Host "WARNING: Could not detect Python process"
    Write-Host "Check if the app started successfully"
    Write-Host "Look for errors in the terminal"
}

Write-Host "`n" + ("=" * 80)
