@echo off
echo ========================================================
echo  Starting EduSense AI - Multimodal Attendance Agent
echo ========================================================

echo [1/3] Running Backend Smoke Test...
cd backend
python smoke_test.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Smoke test failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [2/3] Running Core Acceptance Tests...
python tests/run_tests.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Unit tests failed!
    pause
    exit /b %ERRORLEVEL%
)

echo [3/3] Launching FastAPI Backend on http://localhost:8000...
start cmd /k "python -m uvicorn main:app --reload --port 8000"

echo Launching Frontend Development Server on http://localhost:5173...
cd ..\frontend
start cmd /k "npm run dev"

echo EduSense AI is starting up!
echo - Web Dashboard: http://localhost:5173
echo - API Documentation: http://localhost:8000/docs
echo ========================================================
