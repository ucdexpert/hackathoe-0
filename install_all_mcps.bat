@echo off
REM ============================================================================
REM AI Employee Vault - Install All MCP Servers
REM ============================================================================
REM This script installs all MCP server dependencies
REM
REM Usage: install_all_mcps.bat
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo AI Employee Vault - MCP Server Installation
echo ============================================================================
echo.
echo This will install:
echo   1. Email MCP Server (Gmail SMTP)
echo   2. Social MCP Server (Twitter, Facebook, Instagram)
echo   3. FileOps MCP Server (Browser automation + File operations)
echo   4. Business MCP Server (already installed)
echo.
echo Estimated time: 5-10 minutes
echo.
pause

echo.
echo [Step 1/5] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)
echo [OK] Python found

echo.
echo [Step 2/5] Installing Email MCP Server dependencies...
cd /d "%~dp0mcp\email_mcp"
if exist requirements.txt (
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install Email MCP dependencies
        pause
        exit /b 1
    )
    echo [OK] Email MCP dependencies installed
) else (
    echo [SKIP] requirements.txt not found
)

echo.
echo [Step 3/5] Installing Social MCP Server dependencies...
cd /d "%~dp0mcp\social_mcp"
if exist requirements.txt (
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install Social MCP dependencies
        pause
        exit /b 1
    )
    echo [OK] Social MCP dependencies installed
) else (
    echo [SKIP] requirements.txt not found
)

echo.
echo [Step 4/5] Installing FileOps MCP Server dependencies...
cd /d "%~dp0mcp\fileops_mcp"
if exist requirements.txt (
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install FileOps MCP dependencies
        pause
        exit /b 1
    )
    echo [OK] FileOps MCP dependencies installed
) else (
    echo [SKIP] requirements.txt not found
)

echo.
echo [Step 5/5] Installing Playwright browsers (Chromium)...
playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo WARNING: Playwright installation failed
    echo You can install it later with: playwright install chromium
) else (
    echo [OK] Playwright browsers installed
)

echo.
echo ============================================================================
echo Installation Complete!
echo ============================================================================
echo.
echo Next steps:
echo   1. Copy .env.example to .env
echo   2. Edit .env with your API credentials
echo   3. Restart Claude Desktop
echo.
echo For credential setup, see:
echo   - mcp/email_mcp/README.md
echo   - mcp/social_mcp/API_SETUP_GUIDE.md
echo   - mcp/fileops_mcp/LINKEDIN_AUTOMATION_GUIDE.md
echo.
echo To test MCP servers:
echo   cd mcp/email_mcp && python test_server.py
echo   cd mcp/social_mcp && python test_server.py
echo   cd mcp/fileops_mcp && python test_server.py
echo.
pause
