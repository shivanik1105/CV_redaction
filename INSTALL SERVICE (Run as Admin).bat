@echo off
:: Self-elevate to Administrator
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ================================================
echo   CV Redaction Pipeline - Installing Service
echo ================================================
echo.

set PYTHON=C:\Users\shiva\Downloads\samplecvs\resume\Scripts\python.exe
set SCRIPT=C:\Users\shiva\Downloads\samplecvs\redact_server.py
set WORKDIR=C:\Users\shiva\Downloads\samplecvs

:: Register scheduled task to run at system startup as SYSTEM
schtasks /create /tn "CVRedactionPipeline" /sc onstart /delay 0000:30 ^
  /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
  /ru SYSTEM /rl HIGHEST /f

if %errorLevel% EQU 0 (
    echo [OK] Service task registered.
) else (
    echo [FAIL] Could not register task. Try running this file as Administrator.
    pause
    exit /b 1
)

:: Disable sleep on AC power so the machine stays on
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
echo [OK] Sleep disabled on AC power.

:: Open Windows Firewall port 5000 for private networks
netsh advfirewall firewall delete rule name="CV Redaction Pipeline Port 5000" >nul 2>&1
netsh advfirewall firewall add rule ^
  name="CV Redaction Pipeline Port 5000" ^
  dir=in protocol=tcp localport=5000 action=allow profile=private
echo [OK] Firewall port 5000 opened.

:: Start the task right now (no need to reboot)
schtasks /run /tn "CVRedactionPipeline"
timeout /t 3 /nobreak >nul

:: Print network IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
    set IP=%%a
    goto :done
)
:done
set IP=%IP: =%

echo.
echo ================================================
echo   Share this URL with your team:
echo   http://%IP%:5000
echo ================================================
echo.
echo The server will now start automatically every time
echo this machine boots, even without anyone logging in.
echo.
pause
