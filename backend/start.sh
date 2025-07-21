#!/bin/bash
set -e

export BACKEND_URL=http://localhost:8000
export PORT=${PORT:-3000}
export BACKEND_PORT=${BACKEND_PORT:-8000}

# Start backend in background
echo "Starting backend on port $BACKEND_PORT..."
cd /app/backend/src/chatbot
python ag_ui_server.py &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
until curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; do
    echo "Backend not ready yet, waiting..."
    sleep 1
done
echo "Backend is ready!"

# Start frontend
echo "Starting frontend on port $PORT..."
cd /app/frontend
npm start &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
until curl -f http://localhost:$PORT > /dev/null 2>&1; do
    echo "Frontend not ready yet, waiting..."
    sleep 1
done
echo "Frontend is ready!"

echo "All services started successfully!"
echo "Frontend: http://localhost:$PORT"
echo "Backend: http://localhost:$BACKEND_PORT"

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Keep the container running
wait 