@echo off
REM Quick test batch file for Windows
REM Just double-click this file and enter your PDF path

echo ================================================================================
echo CV REDACTION TEST
echo ================================================================================
echo.

set /p PDF_PATH="Enter the path to your PDF file: "

if not exist "%PDF_PATH%" (
    echo.
    echo Error: File not found: %PDF_PATH%
    echo.
    pause
    exit /b 1
)

echo.
echo Testing CV: %PDF_PATH%
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the test
python quick_test.py "%PDF_PATH%"

echo.
echo ================================================================================
echo Test complete! Check test_redaction_output.txt for full results.
echo ================================================================================
echo.
pause
