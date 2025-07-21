# Multi-stage Dockerfile for CrewAI Flow - Frontend + Backend
# Optimized for Google Cloud Run deployment

# ===========================================
# Stage 1: Build Frontend (Next.js)
# ===========================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci --only=production

# Copy frontend source code
COPY frontend/ ./

# Build the frontend application
RUN npm run build

# ===========================================
# Stage 2: Build Backend (Python)
# ===========================================
FROM python:3.11-slim AS backend-builder

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# ===========================================
# Stage 3: Runtime (Production)
# ===========================================
FROM python:3.11-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python runtime from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend source code
COPY --from=backend-builder /app/backend ./backend

# Copy frontend build from frontend-builder
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/package.json ./frontend/package.json
COPY --from=frontend-builder /app/frontend/next.config.ts ./frontend/next.config.ts

# Install only production frontend dependencies for runtime
WORKDIR /app/frontend
RUN npm ci --only=production

# Create startup script
WORKDIR /app
ENV BACKEND_URL=http://localhost:8000
ENV PORT=3000
ENV BACKEND_PORT=8000
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create a simple health check script
COPY backend/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Set working directory
WORKDIR /app

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Start both services
CMD ["/app/start.sh"] 