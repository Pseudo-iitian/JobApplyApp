#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$ROOT_DIR/backend"

# Ensure .env exists
if [ ! -f "$ROOT_DIR/.env" ] && [ ! -f "$ROOT_DIR/backend/.env" ]; then
    if [ -f "$ROOT_DIR/.env.example" ]; then
        echo "ℹ️  Creating .env from .env.example..."
        cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    fi
fi

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment and installing backend dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "=========================================================="
echo " Starting JobApplyApp FastAPI Backend on http://localhost:8000"
echo " 24/7 Background Scheduler Active"
echo " Swagger Docs: http://localhost:8000/docs"
echo "=========================================================="
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
