@echo off
:: ============================================================
:: CV Redaction Pipeline - One-time setup
:: Double-click this to install. When UAC asks, click YES.
:: ============================================================

:: Step 1 - Self-elevate if not already admin
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Requesting administrator access...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ================================================
echo   CV Redaction Pipeline - Auto-start Setup
echo ================================================
echo.

:: Step 2 - Copy the silent-start VBS to Windows Startup folder
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
copy /y "C:\Users\shiva\Downloads\samplecvs\start_server_silent.vbs" "%STARTUP%\CVRedactionPipeline.vbs"
if %errorLevel% EQU 0 (
    echo [OK] Added to Windows Startup folder.
) else (
    echo [FAIL] Could not add to Startup folder.
)

:: Step 3 - Open firewall port 5000 for local network
netsh advfirewall firewall delete rule name="CV Redaction Pipeline Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="CV Redaction Pipeline Port 5000" dir=in protocol=tcp localport=5000 action=allow profile=private
echo [OK] Firewall port 5000 opened for local network.

:: Step 4 - Disable sleep so PC stays on 24/7
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
echo [OK] PC will no longer sleep on AC power.

:: Step 5 - Start the server right now (no reboot needed)
echo.
echo Starting server now...
wscript "C:\Users\shiva\Downloads\samplecvs\start_server_silent.vbs"
timeout /t 4 /nobreak >nul

:: Step 6 - Print network IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do set IP=%%a
set IP=%IP: =%

echo.
echo ================================================
echo   DONE! Share this URL with your team:
echo   http://%IP%:5000
echo.
echo   The server will now auto-start every time
echo   this PC turns on. You can close this window.
echo ================================================
echo.
pause
