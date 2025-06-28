@echo off
cd /d "C:\Users\avish\OneDrive\Desktop\stem-face-dashboard-main"
"C:\Python313\python.exe" generate_checkins_from_schedule.py
"C:\Python313\python.exe" daily_data_updater.py
pause
