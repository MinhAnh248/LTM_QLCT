@echo off
echo ========================================
echo Starting 3-Layer Expense Manager System
echo ========================================
echo.

echo [1/3] Starting LAN Layer (Backend API)...
start "LAN-Backend" cmd /k "cd LAN && set DATABASE_URL=sqlite:///expense_local.db && set PORT=5001 && set INTERNAL_SECRET=secret-key && set ADMIN_SECRET=admin-secret-key && python app.py"
timeout /t 3

echo [2/3] Starting WAN Layer (Public Web)...
start "WAN-Public" cmd /k "cd WAN && set SECRET_KEY=dev-secret-key && set LAN_API_URL=http://localhost:5001 && set INTERNAL_SECRET=secret-key && set PORT=5500 && python app.py"
timeout /t 3

echo [3/3] Starting VPN Layer (Admin Dashboard)...
start "VPN-Admin" cmd /k "cd VPN && set LAN_API_URL=http://localhost:5001 && set ADMIN_SECRET=admin-secret-key && streamlit run admin_dashboard.py --server.port 8501"
timeout /t 2

echo.
echo ========================================
echo All services started successfully!
echo ========================================
echo.
echo LAN (Backend):  http://localhost:5001
echo WAN (Public):   http://localhost:5500
echo VPN (Admin):    http://localhost:8501
echo.
echo Press any key to open all URLs...
pause

start http://localhost:5001
start http://localhost:5500
start http://localhost:8501

echo.
echo System is running. Close this window to stop all services.
pause
