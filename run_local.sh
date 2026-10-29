#!/usr/bin/env bash
set -e

echo "========================================================"
echo " Starting EduSense AI - Multimodal Attendance Agent"
echo "========================================================"

cd backend
echo "[1/3] Running Backend Smoke Test..."
python smoke_test.py

echo "[2/3] Running Core Acceptance Tests..."
python tests/run_tests.py

echo "[3/3] Launching Backend & Frontend..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "EduSense AI running:"
echo " - Dashboard: http://localhost:5173"
echo " - API Docs:  http://localhost:8000/docs"

wait $BACKEND_PID $FRONTEND_PID
