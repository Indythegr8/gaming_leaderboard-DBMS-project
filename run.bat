@echo off
REM ─────────────────────────────────────────────────────────────
REM Gaming Leaderboard Flask App Launcher
REM ─────────────────────────────────────────────────────────────

chcp 65001 >nul
cls
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║     Gaming Leaderboard - Application Launcher             ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM ─────────────────────────────────────────────────────────────
REM Check if Python is installed
REM ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo [✓] Python found: 
python --version
echo.

REM ─────────────────────────────────────────────────────────────
REM Create virtual environment if it doesn't exist
REM ─────────────────────────────────────────────────────────────
if not exist "venv" (
    echo [•] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment already exists
)
echo.

REM ─────────────────────────────────────────────────────────────
REM Activate virtual environment and install requirements
REM ─────────────────────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [✓] Virtual environment activated
echo.

echo [•] Installing dependencies from requirements.txt...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [✓] Dependencies installed
echo.

REM ─────────────────────────────────────────────────────────────
REM Database Setup Check
REM ─────────────────────────────────────────────────────────────
echo [•] Database Configuration Check
echo    - Make sure your MySQL server is running
echo    - Default connection: localhost, user: root, database: gaming_leaderboard
echo.

REM Optional: You can uncomment the line below to auto-populate the database
REM echo [•] Populating database with sample data...
REM python populate_db.py

REM ─────────────────────────────────────────────────────────────
REM Start the Flask application
REM ─────────────────────────────────────────────────────────────
echo [•] Starting Flask development server...
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║  Server starting on http://127.0.0.1:5000                 ║
echo ║  Press Ctrl+C to stop the server                          ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Set Flask configuration
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start the app
python -m flask run

REM If flask command fails, try direct python execution
if errorlevel 1 (
    echo [•] Trying alternative startup method...
    python app.py
)

pause
