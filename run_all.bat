@echo off
echo ========================================
echo Starting 3-Layer Expense Manager
echo ========================================
echo.

REM Set environment variables
set FLASK_ENV=development
set LAN_API_URL=http://localhost:5001
set DATABASE_URL=postgresql://user:password@localhost:5432/expense_db
set INTERNAL_SECRET=secret-key
set ADMIN_SECRET=admin-secret-key
set SECRET_KEY=your-secret-key

echo [1/3] Starting LAN Layer (Backend API) on port 5001...
start "LAN-API" cmd /k "cd LAN && python app.py"
timeout /t 3 /nobreak >nul

echo [2/3] Starting WAN Layer (Public Web) on port 5000...
start "WAN-Web" cmd /k "cd WAN && python app.py"
timeout /t 3 /nobreak >nul

echo [3/3] Starting VPN Layer (Admin Dashboard) on port 8501...
start "VPN-Admin" cmd /k "cd VPN && streamlit run admin_dashboard.py"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo WAN (Public):  http://localhost:5000
echo LAN (API):     http://localhost:5001
echo VPN (Admin):   http://localhost:8501
echo.
echo Press any key to stop all services...
pause >nul

taskkill /FI "WindowTitle eq LAN-API*" /T /F
taskkill /FI "WindowTitle eq WAN-Web*" /T /F
taskkill /FI "WindowTitle eq VPN-Admin*" /T /F
