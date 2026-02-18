@echo off
REM ============================================================================
REM CEO Weekly Briefing - Windows Task Scheduler Setup
REM ============================================================================
REM This script sets up automatic weekly generation of CEO briefings.
REM Runs every Monday at 8:00 AM.
REM
REM Usage:
REM   setup_ceo_briefing_scheduler.bat [install|uninstall|status]
REM
REM Examples:
REM   setup_ceo_briefing_scheduler.bat install    - Install scheduled task
REM   setup_ceo_briefing_scheduler.bat uninstall  - Remove scheduled task
REM   setup_ceo_briefing_scheduler.bat status     - Show task status
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set BRIEFING_SCRIPT=%SCRIPT_DIR%ceo_briefing.py
set PYTHON_CMD=python
set TASK_NAME=CEO_Weekly_Briefing
set TASK_TIME=08:00
set TASK_DAY=MON

REM Get absolute path to Python
where %PYTHON_CMD% >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python or add it to your system PATH
    exit /b 1
)

for /f "delims=" %%i in ('where %PYTHON_CMD%') do set PYTHON_PATH=%%i
goto :main

:main
if "%~1"=="" goto :menu
if /i "%~1"=="install" goto :install
if /i "%~1"=="uninstall" goto :uninstall
if /i "%~1"=="status" goto :status
if /i "%~1"=="help" goto :help

echo Unknown command: %~1
goto :help

:menu
echo.
echo ============================================================================
echo CEO Weekly Briefing - Task Scheduler Setup
echo ============================================================================
echo.
echo What would you like to do?
echo.
echo   1. Install scheduled task (Every Monday at 8:00 AM)
echo   2. Uninstall scheduled task
echo   3. Show task status
echo   4. Generate briefing now
echo   5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto :install
if "%choice%"=="2" goto :uninstall
if "%choice%"=="3" goto :status
if "%choice%"=="4" goto :generate
if "%choice%"=="5" goto :eof

echo Invalid choice
goto :menu

:install
echo.
echo Installing CEO Weekly Briefing scheduled task...
echo.

REM Create the scheduled task
echo [1/1] Creating task: %TASK_NAME%
schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_PATH%\" \"%BRIEFING_SCRIPT%\" generate" /sc weekly /d %TASK_DAY% /st %TASK_TIME% /ru "%USERNAME%" /rl highest /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       [OK] Task created successfully
) else (
    echo       [ERROR] Failed to create task
    echo       Run this script as Administrator for full functionality
    goto :install_manual
)

echo.
echo ============================================================================
echo Installation Complete!
echo ============================================================================
echo.
echo The CEO Weekly Briefing will now:
echo   - Generate automatically every %TASK_DAY% at %TASK_TIME%
echo   - Save reports to: %SCRIPT_DIR%..\Reports\
echo.
echo To view or manage this task:
echo   1. Open Task Scheduler (taskschd.msc)
echo   2. Find task: %TASK_NAME%
echo.
echo To run manually:
echo   python "%BRIEFING_SCRIPT%" generate
echo.
goto :end

:install_manual
echo.
echo Manual installation required:
echo.
echo 1. Open Task Scheduler (taskschd.msc)
echo 2. Click "Create Basic Task..."
echo 3. Name: %TASK_NAME%
echo 4. Trigger: Weekly
echo 5. Day: Monday
echo 6. Time: %TASK_TIME%
echo 7. Action: Start a program
echo 8. Program: %PYTHON_PATH%
echo 9. Arguments: "%BRIEFING_SCRIPT%" generate
echo.
goto :end

:uninstall
echo.
echo Uninstalling CEO Weekly Briefing scheduled task...
echo.

echo [1/1] Removing task: %TASK_NAME%
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       [OK] Task removed successfully
) else (
    echo       [WARNING] Task not found or could not be removed
)

echo.
echo Uninstallation complete!
echo.
goto :end

:status
echo.
echo ============================================================================
echo CEO Weekly Briefing - Task Status
echo ============================================================================
echo.

echo Checking scheduled task...
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   Status: [OK] Installed
    echo.
    schtasks /query /tn "%TASK_NAME%" | findstr "TaskName Status Next"
) else (
    echo   Status: [ ] Not installed
)

echo.
echo Configuration:
echo   Script: %BRIEFING_SCRIPT%
echo   Python: %PYTHON_PATH%
echo   Schedule: Every %TASK_DAY% at %TASK_TIME%
echo   Reports: %SCRIPT_DIR%..\Reports\
echo.

REM Check if reports directory exists
if exist "%SCRIPT_DIR%..\Reports\" (
    echo Recent Reports:
    echo ----------------------------------------------------------------------------
    dir /b /o-d "%SCRIPT_DIR%..\Reports\" | findstr /i "ceo"
) else (
    echo No reports directory found yet.
)

echo.
goto :end

:generate
echo.
echo Generating CEO Weekly Briefing now...
echo.
python "%BRIEFING_SCRIPT%" generate
goto :end

:help
echo.
echo Usage: setup_ceo_briefing_scheduler.bat [command]
echo.
echo Commands:
echo   install    - Install scheduled task (Every Monday at 8:00 AM)
echo   uninstall  - Remove scheduled task
echo   status     - Show current task status
echo   help       - Show this help message
echo.
echo Without arguments, shows an interactive menu.
echo.
echo Examples:
echo   setup_ceo_briefing_scheduler.bat install
echo   setup_ceo_briefing_scheduler.bat uninstall
echo   setup_ceo_briefing_scheduler.bat status
echo.

:end
echo ============================================================================
endlocal
exit /b 0
