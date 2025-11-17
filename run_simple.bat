@echo off
echo ========================================
echo Quick Start - Expense Manager
echo ========================================
echo.

REM Set environment variables
set LAN_API_URL=http://localhost:5001
set INTERNAL_SECRET=secret-key
set ADMIN_SECRET=admin-secret-key

echo Starting LAN API (Backend)...
cd LAN
start "LAN-Backend" python app.py
cd ..

timeout /t 5 /nobreak >nul

echo Starting WAN Web (Frontend)...
cd WAN
start "WAN-Frontend" python app.py
cd ..

echo.
echo ========================================
echo Services Running:
echo ========================================
echo WAN (Users):  http://localhost:5000
echo LAN (API):    http://localhost:5001
echo.
echo Press Ctrl+C in each window to stop
echo ========================================
