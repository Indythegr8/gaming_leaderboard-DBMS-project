@echo off
setlocal enabledelayedexpansion

REM ═════════════════════════════════════════════════════════════
REM Gaming Leaderboard - Flask App Launcher & Setup
REM ═════════════════════════════════════════════════════════════

chcp 65001 >nul
cls

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║   Gaming Leaderboard - Flask Application                  ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM ─────────────────────────────────────────────────────────────
REM Check if Python is installed
REM ─────────────────────────────────────────────────────────────
echo [•] Checking Python installation...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Python not found in PATH
    echo Please install Python: https://www.python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo [✓] !PYTHON_VER!
echo.

REM ─────────────────────────────────────────────────────────────
REM Create/Check virtual environment
REM ─────────────────────────────────────────────────────────────
echo [•] Checking virtual environment...
if not exist "venv" (
    echo    Creating venv. This may take a moment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo.
        echo [ERROR] Failed to create venv
        echo.
        pause
        exit /b 1
    )
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment exists
)
echo.

REM ─────────────────────────────────────────────────────────────
REM Activate virtual environment
REM ─────────────────────────────────────────────────────────────
echo [•] Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to activate venv
    echo.
    pause
    exit /b 1
)
echo [✓] Activated
echo.

REM ─────────────────────────────────────────────────────────────
REM Install dependencies
REM ─────────────────────────────────────────────────────────────
echo [•] Installing dependencies from requirements.txt...
pip install -q -r requirements.txt
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Try: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo [✓] Dependencies installed
echo.

REM ─────────────────────────────────────────────────────────────
REM Create .env if missing
REM ─────────────────────────────────────────────────────────────
if not exist ".env" (
    echo [•] Creating .env file...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [✓] .env created
    ) else (
        echo [ERROR] .env.example not found
        echo.
        pause
        exit /b 1
    )
)
echo.

REM ─────────────────────────────────────────────────────────────
REM Setup database if first run
REM ─────────────────────────────────────────────────────────────
if not exist "setup_done.txt" (
    echo [!] First run - Database setup needed
    echo.
    set /p PROCEED="Continue with database setup? (y/n): "
    
    if /i "!PROCEED!"=="y" (
        echo.
        echo [•] Reading .env credentials...
        
        REM Parse .env for DB_PASSWORD
        for /f "tokens=2 delims==" %%A in ('findstr /R "^DB_PASSWORD" .env') do set DB_PASS=%%A
        
        if "!DB_PASS!"=="" (
            echo [ERROR] Could not read DB_PASSWORD from .env
            echo.
            pause
            exit /b 1
        )
        
        echo [•] Creating database 'gaming_leaderboard'...
        set PGPASSWORD=!DB_PASS!
        psql -U postgres -h localhost -c "CREATE DATABASE gaming_leaderboard;" 2>nul
        if !errorlevel! equ 0 (
            echo [✓] Database created
        ) else (
            echo [!] Database may already exist (checking...)
        )
        echo.
        
        echo [•] Initializing tables and seed data...
        psql -U postgres -h localhost -d gaming_leaderboard -f schema.sql >nul 2>&1
        if !errorlevel! equ 0 (
            echo [✓] Tables initialized
            echo. > setup_done.txt
        ) else (
            echo [ERROR] Schema initialization failed
            echo Try manually: psql -U postgres -d gaming_leaderboard -f schema.sql
            echo.
            pause
            exit /b 1
        )
    )
    echo.
)

REM ─────────────────────────────────────────────────────────────
REM Start Flask
REM ─────────────────────────────────────────────────────────────
echo ╔═══════════════════════════════════════════════════════════╗
echo ║   Flask Server Starting                                   ║
echo ║   URL: http://127.0.0.1:5000                              ║
echo ║   Press Ctrl+C to stop                                    ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

python -m flask run

echo.
echo [•] Flask stopped
pause
exit /b 0


