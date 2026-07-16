@echo off
title FirstLight AI Studio

echo Starting FirstLight AI Studio...
echo.

start "" "D:\FirstLight-AI\launcher\Start-Backend.bat"

timeout /t 3 >nul

start "" "D:\FirstLight-AI\launcher\Start-Frontend.bat"

timeout /t 3 >nul

start "" "D:\FirstLight-AI\launcher\Start-Developer.bat"

timeout /t 2 >nul

code D:\FirstLight-AI

timeout /t 5 >nul

start "" http://127.0.0.1:8000/docs
start "" http://localhost:3000

echo.
echo ==========================================
echo FirstLight AI Studio Started Successfully
echo ==========================================

timeout /t 3 >nul
exit