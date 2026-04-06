@echo off
REM CV Redactor - Drag & Drop Interface
REM Drag a folder onto this file to process all CVs inside

echo ============================================================
echo           CV REDACTOR - Drag ^& Drop
echo ============================================================
echo.

REM Check if a folder was dragged
if "%~1"=="" (
    echo ERROR: No folder provided!
    echo.
    echo HOW TO USE:
    echo   1. Drag a folder containing CVs onto this file
    echo   2. The CVs will be processed automatically
    echo   3. Output will be in a new "Redacted" subfolder
    echo.
    echo EXAMPLE:
    echo   Drag: C:\CVs\Original
    echo   Output: C:\CVs\Original\Redacted
    echo.
    pause
    exit /b 1
)

REM Get input folder
set "INPUT_FOLDER=%~1"

REM Check if it's a folder
if not exist "%INPUT_FOLDER%\" (
    echo ERROR: "%INPUT_FOLDER%" is not a valid folder!
    echo.
    pause
    exit /b 1
)

REM Create output folder
set "OUTPUT_FOLDER=%INPUT_FOLDER%\Redacted"
if not exist "%OUTPUT_FOLDER%" mkdir "%OUTPUT_FOLDER%"

echo Input folder:  %INPUT_FOLDER%
echo Output folder: %OUTPUT_FOLDER%
echo.
echo Processing CVs...
echo This may take a few minutes depending on the number of files.
echo.

REM Run CVRedactor
CVRedactor.exe "%INPUT_FOLDER%" "%OUTPUT_FOLDER%"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Processing failed!
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! CVs have been anonymized.
echo ============================================================
echo.
echo Anonymized CVs are in: %OUTPUT_FOLDER%
echo.
echo You can now:
echo   1. Review the anonymized CVs
echo   2. Share them with clients
echo   3. Store them in your database
echo.
pause
