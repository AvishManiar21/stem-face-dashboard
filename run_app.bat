@echo off
echo Setting up Supabase environment variables...
set SUPABASE_URL=https://irjcbxhnowqegrsqludr.supabase.co
set SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlyamNieGhub3dxZWdyc3FsdWRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAyOTI5NTQsImV4cCI6MjA2NTg2ODk1NH0.8goc4vrlf4IsxawfnMPFhLYnVcp-80o6nJrmmzp1Ry0

echo Environment variables set:
echo SUPABASE_URL=%SUPABASE_URL%
echo SUPABASE_KEY=%SUPABASE_KEY:~0,20%...

echo Starting Flask application...
python app.py
pause 