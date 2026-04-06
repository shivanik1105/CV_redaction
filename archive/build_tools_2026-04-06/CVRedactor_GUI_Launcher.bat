@echo off
REM CV Redactor - Easy Launcher
REM Double-click this file to use CV Redactor with a simple menu

:MENU
cls
echo ============================================================
echo           CV REDACTOR - Easy Launcher
echo ============================================================
echo.
echo What would you like to do?
echo.
echo 1. Process CVs (Redact PII)
echo 2. Add City to Configuration
echo 3. Add Technical Term to Configuration
echo 4. View Configuration
echo 5. Show Help
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto PROCESS
if "%choice%"=="2" goto ADD_CITY
if "%choice%"=="3" goto ADD_TERM
if "%choice%"=="4" goto VIEW_CONFIG
if "%choice%"=="5" goto HELP
if "%choice%"=="6" goto EXIT
goto MENU

:PROCESS
cls
echo ============================================================
echo           PROCESS CVs
echo ============================================================
echo.
set /p input="Enter input folder path (e.g., C:\CVs\Input): "
set /p output="Enter output folder path (e.g., C:\CVs\Output): "
echo.
echo Processing CVs...
echo Input:  %input%
echo Output: %output%
echo.
CVRedactor.exe "%input%" "%output%"
echo.
echo Done! Press any key to return to menu...
pause >nul
goto MENU

:ADD_CITY
cls
echo ============================================================
echo           ADD CITY
echo ============================================================
echo.
set /p city="Enter city name (e.g., Boston): "
echo.
CVRedactor.exe add-city "%city%"
echo.
pause
goto MENU

:ADD_TERM
cls
echo ============================================================
echo           ADD TECHNICAL TERM
echo ============================================================
echo.
set /p term="Enter technical term (e.g., python, docker): "
echo.
CVRedactor.exe add-term "%term%"
echo.
pause
goto MENU

:VIEW_CONFIG
cls
echo ============================================================
echo           CONFIGURATION SUMMARY
echo ============================================================
echo.
CVRedactor.exe list-config
echo.
pause
goto MENU

:HELP
cls
echo ============================================================
echo           CV REDACTOR - HELP
echo ============================================================
echo.
echo CV Redactor removes personal information from CVs.
echo.
echo WHAT IT REMOVES:
echo   - Names
echo   - Email addresses
echo   - Phone numbers
echo   - Physical addresses
echo   - Dates of birth
echo.
echo WHAT IT KEEPS:
echo   - Technical skills
echo   - Work experience
echo   - Education
echo   - Certifications
echo.
echo HOW TO USE:
echo   1. Put your CVs (PDF or DOCX) in a folder
echo   2. Choose option 1 from the menu
echo   3. Enter input folder path
echo   4. Enter output folder path
echo   5. Wait for processing to complete
echo   6. Find anonymized CVs in output folder
echo.
echo EXAMPLE:
echo   Input:  C:\CVs\Original
echo   Output: C:\CVs\Anonymized
echo.
pause
goto MENU

:EXIT
cls
echo.
echo Thank you for using CV Redactor!
echo.
timeout /t 2 >nul
exit
