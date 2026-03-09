# ============================================================
# CV Redaction Pipeline — Install as Windows Service
# Run this ONCE as Administrator to make the server always-on
# ============================================================
# Right-click install_service.ps1 → "Run with PowerShell as Administrator"

$taskName   = "CVRedactionPipeline"
$pythonExe  = "C:\Users\shiva\Downloads\samplecvs\resume\Scripts\python.exe"
$scriptPath = "C:\Users\shiva\Downloads\samplecvs\redact_server.py"
$workDir    = "C:\Users\shiva\Downloads\samplecvs"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  CV Redaction Pipeline — Service Installer" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Validate paths ─────────────────────────────────────
if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python not found at $pythonExe" -ForegroundColor Red
    Write-Host "Run this from the project folder after activating the venv." -ForegroundColor Yellow
    pause; exit 1
}
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: redact_server.py not found at $scriptPath" -ForegroundColor Red
    pause; exit 1
}

# ── 2. Remove old task if it exists ───────────────────────
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "Removed any previous task (if any)." -ForegroundColor Gray

# ── 3. Create the scheduled task ──────────────────────────
$action = New-ScheduledTaskAction `
    -Execute   $pythonExe `
    -Argument  $scriptPath `
    -WorkingDirectory $workDir

# Trigger: run at system startup
$trigger = New-ScheduledTaskTrigger -AtStartup

# Settings: no time limit, auto-restart if it crashes (up to 3 times)
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit      (New-TimeSpan -Days 3650) `
    -RestartCount            3 `
    -RestartInterval         (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable      $true `
    -RunOnlyIfNetworkAvailable $false

# Run as SYSTEM so it works even when no one is logged in
$principal = New-ScheduledTaskPrincipal `
    -UserId    "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel  Highest

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host "Task registered: '$taskName'" -ForegroundColor Green

# ── 4. Prevent the machine from sleeping ──────────────────
powercfg /change standby-timeout-ac 0    # never sleep on AC power
powercfg /change monitor-timeout-ac 0   # screen can sleep but PC stays on
Write-Host "Sleep disabled on AC power." -ForegroundColor Green

# ── 5. Open firewall port 5000 ───────────────────────────
$ruleName = "CV Redaction Pipeline Port 5000"
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
New-NetFirewallRule `
    -DisplayName  $ruleName `
    -Direction    Inbound `
    -Protocol     TCP `
    -LocalPort    5000 `
    -Action       Allow `
    -Profile      Private `
    -Description  "Allow recruiters on LAN to access CV Redaction Pipeline" | Out-Null
Write-Host "Firewall rule added for port 5000 (Private network)." -ForegroundColor Green

# ── 6. Start the task immediately (don't wait for next reboot) ──
Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 3

$state = (Get-ScheduledTask -TaskName $taskName).State
Write-Host ""
if ($state -eq "Running") {
    Write-Host "Service is RUNNING now!" -ForegroundColor Green
} else {
    Write-Host "Task state: $state  (it will start on next reboot if not running now)" -ForegroundColor Yellow
}

# ── 7. Print the network URL ─────────────────────────────
$ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "*" | 
       Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } | 
       Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Share this URL with your team:" -ForegroundColor Cyan
Write-Host "  http://$($ip):5000" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The server will now start automatically every time" -ForegroundColor Gray
Write-Host "this machine boots, even without anyone logging in." -ForegroundColor Gray
Write-Host ""
pause
