@echo off
cd /d "C:\Agent RAB Analyzer\backend_fastapi"
py -m uvicorn app.main:app --reload --port 8000
pause
