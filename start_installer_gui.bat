@echo off
SETLOCAL

:: RT1018 Installer GUI Launcher
:: Double-click this file to start the installer

echo ================================================
echo   RT1018 Android Device Installer - GUI
echo ================================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [INFO] Please install Python 3.7 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found
python --version

:: Check if ADB is installed
adb version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] ADB is not installed or not in PATH
    echo [INFO] Please install Android Platform Tools from:
    echo [INFO] https://developer.android.com/studio/releases/platform-tools
    echo.
    echo [ACTION] The GUI will start, but you won't be able to connect to devices without ADB
    echo.
    timeout /t 5
)

echo.
echo [INFO] Starting RT1018 Installer GUI...
echo.

:: Run the GUI application
python rt1018_installer_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start the application
    echo.
    pause
)

ENDLOCAL
