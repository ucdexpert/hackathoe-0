@echo off
REM ============================================================================
REM Business MCP Server - Windows Task Scheduler Setup
REM ============================================================================
REM This script creates scheduled tasks to run the Business MCP Server
REM automatically on Windows startup and at scheduled intervals.
REM
REM Usage:
REM   setup_task_scheduler.bat [install|uninstall|status]
REM
REM Examples:
REM   setup_task_scheduler.bat install    - Install scheduled tasks
REM   setup_task_scheduler.bat uninstall  - Remove scheduled tasks
REM   setup_task_scheduler.bat status     - Show task status
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set SCRIPT_DIR=%~dp0
set SERVER_SCRIPT=%SCRIPT_DIR%server.py
set PYTHON_CMD=python
set TASK_NAME_STARTUP=BusinessMCP-Startup
set TASK_NAME_HOURLY=BusinessMCP-Hourly
set LOG_FILE=%SCRIPT_DIR%mcp_server.log

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
echo Business MCP Server - Task Scheduler Setup
echo ============================================================================
echo.
echo What would you like to do?
echo.
echo   1. Install scheduled tasks
echo   2. Uninstall scheduled tasks
echo   3. Show task status
echo   4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto :install
if "%choice%"=="2" goto :uninstall
if "%choice%"=="3" goto :status
if "%choice%"=="4" goto :eof

echo Invalid choice
goto :menu

:install
echo.
echo Installing Business MCP Server scheduled tasks...
echo.

REM Create startup task (runs when user logs in)
echo [1/2] Creating startup task...
schtasks /create /tn "%TASK_NAME_STARTUP%" /tr "\"%PYTHON_PATH%\" \"%SERVER_SCRIPT%\"" /sc onlogon /ru "%USERNAME%" /rl highest /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       ✓ Startup task created successfully
) else (
    echo       ✗ Failed to create startup task
    echo       Run this script as Administrator for full functionality
)

REM Create hourly check task
echo [2/2] Creating hourly check task...
schtasks /create /tn "%TASK_NAME_HOURLY%" /tr "\"%PYTHON_PATH%\" \"%SERVER_SCRIPT%\" --status" /sc hourly /ru "%USERNAME%" /rl highest /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       ✓ Hourly task created successfully
) else (
    echo       ✗ Failed to create hourly task
    echo       Run this script as Administrator for full functionality
)

echo.
echo Installation complete!
echo.
echo The Business MCP Server will now:
echo   - Start when you log in
echo   - Run status check every hour
echo.
echo To view logs: %LOG_FILE%
echo To manage tasks: Open Task Scheduler (taskschd.msc)
echo.
goto :end

:uninstall
echo.
echo Uninstalling Business MCP Server scheduled tasks...
echo.

echo [1/2] Removing startup task...
schtasks /delete /tn "%TASK_NAME_STARTUP%" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       ✓ Startup task removed
) else (
    echo       ✗ Startup task not found or could not be removed
)

echo [2/2] Removing hourly task...
schtasks /delete /tn "%TASK_NAME_HOURLY%" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo       ✓ Hourly task removed
) else (
    echo       ✗ Hourly task not found or could not be removed
)

echo.
echo Uninstallation complete!
echo.
goto :end

:status
echo.
echo ============================================================================
echo Business MCP Server - Task Status
echo ============================================================================
echo.

echo Checking startup task...
schtasks /query /tn "%TASK_NAME_STARTUP%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   Status: ✓ Installed
    schtasks /query /tn "%TASK_NAME_STARTUP%" | findstr "Status Next"
) else (
    echo   Status: ✗ Not installed
)

echo.
echo Checking hourly task...
schtasks /query /tn "%TASK_NAME_HOURLY%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   Status: ✓ Installed
    schtasks /query /tn "%TASK_NAME_HOURLY%" | findstr "Status Next"
) else (
    echo   Status: ✗ Not installed
)

echo.
echo Server Configuration:
echo   Script: %SERVER_SCRIPT%
echo   Python: %PYTHON_PATH%
echo   Log:    %LOG_FILE%
echo.

if exist "%LOG_FILE%" (
    echo Recent log entries:
    echo ----------------------------------------------------------------------------
    powershell -Command "Get-Content '%LOG_FILE%' -Tail 5"
) else (
    echo No log file found yet.
)

echo.
goto :end

:help
echo.
echo Usage: setup_task_scheduler.bat [command]
echo.
echo Commands:
echo   install    - Install scheduled tasks (requires Administrator for full access)
echo   uninstall  - Remove scheduled tasks
echo   status     - Show current task status
echo   help       - Show this help message
echo.
echo Without arguments, shows an interactive menu.
echo.
echo Examples:
echo   setup_task_scheduler.bat install
echo   setup_task_scheduler.bat uninstall
echo   setup_task_scheduler.bat status
echo.

:end
echo ============================================================================
endlocal
exit /b 0
