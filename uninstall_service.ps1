# ============================================================
# CV Redaction Pipeline — Uninstall Windows Service
# Run as Administrator if you want to remove the auto-start
# ============================================================

$taskName = "CVRedactionPipeline"
$ruleName = "CV Redaction Pipeline Port 5000"

Write-Host ""
Write-Host "Stopping and removing CV Redaction Pipeline service..." -ForegroundColor Yellow

Stop-ScheduledTask  -TaskName $taskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

Write-Host "Done. The service has been removed." -ForegroundColor Green
Write-Host "You can still run it manually with: python redact_server.py" -ForegroundColor Gray
Write-Host ""
pause
