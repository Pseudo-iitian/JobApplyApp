#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$ROOT_DIR/frontend"

# Ensure node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "=========================================================="
echo " Starting JobApplyApp Frontend on http://localhost:5173"
echo " Jira-like Kanban Application Tracking System"
echo "=========================================================="
npm run dev
