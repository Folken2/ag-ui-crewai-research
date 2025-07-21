# syntax=docker/dockerfile:1

############################################
# Stage 1: Build Frontend (Next.js)
############################################
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build in standalone mode
COPY frontend/ ./
RUN npm run build

############################################
# Stage 2: Build Backend (Python)
############################################
FROM python:3.11-slim AS backend-builder

WORKDIR /app/backend

# Install system build dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

############################################
# Stage 3: Runtime Image
############################################
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

### Copy Python runtime from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /app/backend ./backend

### Copy Next.js standalone output 
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static

# Copy start and healthcheck scripts
COPY backend/start.sh /app/start.sh
COPY backend/healthcheck.sh /app/healthcheck.sh

# Make scripts executable
RUN chmod +x /app/*.sh

# Cloud Run expects app to listen on 8080
ENV PORT=8080
ENV BACKEND_PORT=8000

# Expose ingress port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD ["/app/healthcheck.sh"]

# Start both services
CMD ["/app/start.sh"]
