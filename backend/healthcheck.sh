#!/bin/bash
FRONTEND_PORT=${PORT:-3000}
BACKEND_PORT=${BACKEND_PORT:-8000}

# Check backend
if ! curl -f http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
    echo "Backend health check failed"
    exit 1
fi

# Check frontend
if ! curl -f http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
    echo "Frontend health check failed"
    exit 1
fi

echo "All services healthy"
exit 0 