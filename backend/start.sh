#!/bin/bash
set -e

# Set defaults
export PORT=${PORT:-8080}
export BACKEND_PORT=${BACKEND_PORT:-8000}

echo "🧠 Starting Python backend on $BACKEND_PORT..."
cd /app/backend/src/chatbot
python ag_ui_server.py &
BACKEND_PID=$!

echo "🌐 Waiting for backend to be ready..."
until curl -sSf http://localhost:$BACKEND_PORT/health > /dev/null; do
  echo "Waiting for backend..."
  sleep 1
done
echo "✅ Backend ready!"

echo "🪄 Starting Next.js frontend on $PORT..."
cd /app/frontend
node server.js --port $PORT &
FRONTEND_PID=$!

trap "echo '🛑 Stopping...'; kill $BACKEND_PID $FRONTEND_PID;" SIGINT SIGTERM

wait
