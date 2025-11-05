@echo off
echo Starting LAN Server...
set DATABASE_URL=sqlite:///expense_local.db
set PORT=5001
set INTERNAL_SECRET=secret-key
set ADMIN_SECRET=admin-secret-key
python app.py
pause