#!/usr/bin/env bash
set -e

echo "Starting Multi-LLM Synthesis Platform..."

# 1. Ensure backend .env exists
if [ ! -f "backend/.env" ]; then
    echo "[INFO] Copying .env.example -> backend/.env"
    cp .env.example backend/.env
fi

# 2. Start backend
echo "[BACKEND] Starting FastAPI on http://localhost:8000 ..."
cd backend
source venv/bin/activate 2>/dev/null || true
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 3. Start frontend
echo "[FRONTEND] Starting Vite dev server on http://localhost:5173 ..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=============================="
echo " System started successfully!"
echo "=============================="
echo " Frontend : http://localhost:5173"
echo " API      : http://localhost:8000"
echo " API Docs : http://localhost:8000/docs"
echo " Health   : http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'; exit 0" SIGINT SIGTERM

wait
