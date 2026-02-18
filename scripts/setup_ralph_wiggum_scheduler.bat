@echo off
REM ============================================================================
REM Ralph Wiggum Autonomous Loop - Windows Task Scheduler Setup
REM ============================================================================
REM This script sets up automatic task execution via Ralph Wiggum loop.
REM Runs every hour to process pending tasks.
REM
REM Usage:
REM   setup_ralph_wiggum_scheduler.bat [install|uninstall|status]
REM
REM Examples:
REM   setup_ralph_wiggum_scheduler.bat install    - Install scheduled task
REM   setup_ralph_wiggum_scheduler.bat uninstall  - Remove scheduled task
REM   setup_ralph_wiggum_scheduler.bat status     - Show task status
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set RALPH_SCRIPT=%SCRIPT_DIR%ralph_wiggum.py
set PYTHON_CMD=python
set TASK_NAME=Ralph_Wiggum_Autonomous_Loop
set TASK_SCHEDULE=hourly

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
echo Ralph Wiggum Autonomous Loop - Task Scheduler Setup
echo ============================================================================
echo.
echo What would you like to do?
echo.
echo   1. Install scheduled task (Every hour)
echo   2. Uninstall scheduled task
echo   3. Show task status
echo   4. Run Ralph Wiggum now
echo   5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto :install
if "%choice%"=="2" goto :uninstall
if "%choice%"=="3" goto :status
if "%choice%"=="4" goto :run
if "%choice%"=="5" goto :eof

echo Invalid choice
goto :menu

:install
echo.
echo Installing Ralph Wiggum Autonomous Loop scheduled task...
echo.

echo [1/1] Creating task: %TASK_NAME%
schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_PATH%\" \"%RALPH_SCRIPT%\" run" /sc %TASK_SCHEDULE% /ru "%USERNAME%" /rl highest /f >nul 2>&1
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
echo The Ralph Wiggum Autonomous Loop will now:
echo   - Run automatically %TASK_SCHEDULE%
echo   - Process tasks from Needs_Action folder
echo   - Create plans and execute steps autonomously
echo   - Move completed tasks to Done folder
echo.
echo To view or manage this task:
echo   1. Open Task Scheduler (taskschd.msc)
echo   2. Find task: %TASK_NAME%
echo.
echo To run manually:
echo   python "%RALPH_SCRIPT%" run
echo.
goto :end

:install_manual
echo.
echo Manual installation required:
echo.
echo 1. Open Task Scheduler (taskschd.msc)
echo 2. Click "Create Basic Task..."
echo 3. Name: %TASK_NAME%
echo 4. Trigger: %TASK_SCHEDULE%
echo 5. Action: Start a program
echo 6. Program: %PYTHON_PATH%
echo 7. Arguments: "%RALPH_SCRIPT%" run
echo.
goto :end

:uninstall
echo.
echo Uninstalling Ralph Wiggum Autonomous Loop scheduled task...
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
echo Ralph Wiggum Autonomous Loop - Task Status
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
echo   Script: %RALPH_SCRIPT%
echo   Python: %PYTHON_PATH%
echo   Schedule: %TASK_SCHEDULE%
echo   Vault: %SCRIPT_DIR%..
echo.

REM Check logs
if exist "%SCRIPT_DIR%..\Logs\ralph_wiggum.log" (
    echo Recent Activity:
    echo ----------------------------------------------------------------------------
    powershell -Command "Get-Content '%SCRIPT_DIR%..\Logs\ralph_wiggum.log' -Tail 5 | ForEach-Object { $_ }"
) else (
    echo No activity logs found yet.
)

echo.
goto :end

:run
echo.
echo Running Ralph Wiggum Autonomous Loop now...
echo.
python "%RALPH_SCRIPT%" run
goto :end

:help
echo.
echo Usage: setup_ralph_wiggum_scheduler.bat [command]
echo.
echo Commands:
echo   install    - Install scheduled task (Every hour)
echo   uninstall  - Remove scheduled task
echo   status     - Show current task status
echo   help       - Show this help message
echo.
echo Without arguments, shows an interactive menu.
echo.
echo Examples:
echo   setup_ralph_wiggum_scheduler.bat install
echo   setup_ralph_wiggum_scheduler.bat uninstall
echo   setup_ralph_wiggum_scheduler.bat status
echo.

:end
echo ============================================================================
endlocal
exit /b 0
