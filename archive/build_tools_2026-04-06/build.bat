@echo off
REM Build script for CV Intelligence System Windows executable
REM Run this to create CVIntelligence.exe

echo ============================================================
echo Building CV Intelligence System .exe
echo ============================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo Building executable...
echo This may take 5-10 minutes...
echo.

REM Build using spec file
pyinstaller build_installer.spec

if errorlevel 1 (
    echo.
    echo ============================================================
    echo Build FAILED!
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build SUCCESSFUL!
echo ============================================================
echo.
echo Executable location: dist\CVIntelligence.exe
echo.
echo Next steps:
echo 1. Test: dist\CVIntelligence.exe
echo 2. Distribute to users
echo.
pause
