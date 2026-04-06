@echo off
REM Build script for CV Redactor standalone executable
REM This builds ONLY the redaction component (no LLM, no database, no web)

echo ============================================================
echo Building CV Redactor Standalone Executable
echo ============================================================
echo.

REM Check if PyInstaller is installed
echo Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
) else (
    echo PyInstaller found
)

REM Check if spaCy model is installed
echo.
echo Checking spaCy model...
python -c "import en_core_web_sm" 2>nul
if errorlevel 1 (
    echo Installing spaCy model...
    python -m spacy download en_core_web_sm
) else (
    echo spaCy model found
)

REM Clean previous builds
echo.
echo Cleaning previous builds...
if exist dist\CVRedactor.exe (
    del /f /q dist\CVRedactor.exe
    echo Removed old CVRedactor.exe
)
if exist build (
    rmdir /s /q build
    echo Removed build/
)

echo.
echo Building CV Redactor executable...
echo This may take 5-10 minutes...
echo.

REM Build using spec file
pyinstaller build_cv_redactor.spec --clean

if errorlevel 1 (
    echo.
    echo ============================================================
    echo Build FAILED!
    echo ============================================================
    echo.
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build SUCCESSFUL!
echo ============================================================
echo.

if exist dist\CVRedactor.exe (
    echo Executable location: dist\CVRedactor.exe
    for %%A in (dist\CVRedactor.exe) do echo File size: %%~zA bytes
)

echo.
echo What this .exe does:
echo   - Redacts PII from CVs (names, emails, phones, addresses)
echo   - Processes PDF and DOCX files
echo   - Outputs anonymized text files
echo   - NO LLM, NO database, NO web interface
echo   - Pure standalone redaction tool

echo.
echo Usage examples:
echo   dist\CVRedactor.exe resume\ output\
echo   dist\CVRedactor.exe add-city "Boston"
echo   dist\CVRedactor.exe list-config

echo.
echo Next steps:
echo 1. Test: dist\CVRedactor.exe --help
echo 2. Process CVs: dist\CVRedactor.exe resume\ output\
echo 3. Distribute: Share dist\CVRedactor.exe

echo.
pause
