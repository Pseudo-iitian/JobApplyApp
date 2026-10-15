#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

echo "=========================================================="
echo "      🚀 Launching JobApplyApp (AI Job Hunter & ATS)     "
echo "=========================================================="

trap 'kill 0' EXIT

# Ensure environment file exists
if [ ! -f "$DIR/.env" ] && [ ! -f "$DIR/backend/.env" ]; then
    if [ -f "$DIR/.env.example" ]; then
        echo "ℹ️  No .env file found. Creating .env from .env.example..."
        cp "$DIR/.env.example" "$DIR/.env"
    fi
fi

# Setup backend virtual environment if missing
if [ ! -d "$DIR/backend/venv" ]; then
    echo "⚠️  backend/venv not found. Creating virtualenv and installing dependencies..."
    python3 -m venv "$DIR/backend/venv"
    source "$DIR/backend/venv/bin/activate"
    pip install -r "$DIR/backend/requirements.txt"
else
    source "$DIR/backend/venv/bin/activate"
fi

# Start backend
echo "▶ Starting Backend Server on http://localhost:8000..."
cd "$DIR/backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Setup frontend dependencies if missing
if [ ! -d "$DIR/frontend/node_modules" ]; then
    echo "⚠️  frontend/node_modules not found. Installing npm dependencies..."
    cd "$DIR/frontend" && npm install
fi

# Start frontend
echo "▶ Starting Frontend Client on http://localhost:5173..."
cd "$DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo "✔ Backend running on:  http://localhost:8000"
echo "✔ Swagger API Docs on: http://localhost:8000/docs"
echo "✔ Frontend UI on:      http://localhost:5173"
echo "✔ 24/7 Scheduler:      ACTIVE"
echo "=========================================================="
echo "Press Ctrl+C to stop all servers."
echo ""

wait
