@echo off
setlocal EnableDelayedExpansion
title FIRSTLIGHT AI STUDIO v1.0
color 0A

:: ==========================================================
:: Configuration
:: ==========================================================
set ROOT=D:\FirstLight-AI
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend
set VENV=%ROOT%\.venv\Scripts\Activate.ps1

echo.
echo ===============================================================
echo                 FIRSTLIGHT AI STUDIO v1.0
echo ===============================================================
echo.

:: ---------------------------------------------------------------
:: Check Python
:: ---------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python is not installed.
    pause
    exit /b
)

:: ---------------------------------------------------------------
:: Check Node
:: ---------------------------------------------------------------
node -v >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Node.js is not installed.
    pause
    exit /b
)

:: ---------------------------------------------------------------
:: Check npm
:: ---------------------------------------------------------------
npm -v >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] npm is not installed.
    pause
    exit /b
)

:: ---------------------------------------------------------------
:: Check Git
:: ---------------------------------------------------------------
git --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Git is not installed.
    pause
    exit /b
)

:: ---------------------------------------------------------------
:: Check Virtual Environment
:: ---------------------------------------------------------------
if not exist "%VENV%" (
    color 0C
    echo [ERROR] Virtual Environment not found.
    pause
    exit /b
)

:: ---------------------------------------------------------------
:: Check Backend
:: ---------------------------------------------------------------
if not exist "%BACKEND%\app\main.py" (
    color 0C
    echo [ERROR] Backend missing.
    pause
    exit /b
)

:: ---------------------------------------------------------------
:: Check Frontend
:: ---------------------------------------------------------------
if not exist "%FRONTEND%\package.json" (
    color 0C
    echo [ERROR] Frontend missing.
    pause
    exit /b
)

echo.
echo ===============================================================
echo                 ALL CHECKS PASSED
echo ===============================================================
echo.

:: ===============================================================
:: Backend
:: ===============================================================
echo Starting Backend...
start "FirstLight Backend" powershell.exe -NoExit -ExecutionPolicy Bypass -Command ^
"cd '%BACKEND%'; ^
& '%VENV%'; ^
python -m uvicorn app.main:app --reload"

timeout /t 5 >nul

:: ===============================================================
:: Frontend
:: ===============================================================
echo Starting Frontend...
start "FirstLight Frontend" powershell.exe -NoExit -ExecutionPolicy Bypass -Command ^
"cd '%FRONTEND%'; ^
npm run dev"

timeout /t 5 >nul

:: ===============================================================
:: Developer Terminal
:: ===============================================================
echo Opening Developer Terminal...
start "FirstLight Developer" powershell.exe -NoExit -ExecutionPolicy Bypass -Command ^
"cd '%BACKEND%'; ^
& '%VENV%'"

timeout /t 2 >nul

:: ===============================================================
:: VS Code
:: ===============================================================
where code >nul 2>&1
if not errorlevel 1 (
    echo Opening VS Code...
    start "" code "%ROOT%"
)

:: ===============================================================
:: Browser
:: ===============================================================
timeout /t 5 >nul

echo Opening Swagger...
start "" http://127.0.0.1:8000/docs

echo Opening Frontend...
start "" http://localhost:3000

echo.
echo ===============================================================
echo               FIRSTLIGHT AI STUDIO READY
echo ===============================================================
echo.
echo Backend   : http://127.0.0.1:8000
echo Swagger   : http://127.0.0.1:8000/docs
echo Frontend  : http://localhost:3000
echo.
echo Happy Coding!
echo.

exit