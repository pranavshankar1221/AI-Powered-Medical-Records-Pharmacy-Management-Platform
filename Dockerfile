# ============================================================
# Stage 1: Build React frontend
# ============================================================

FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


# ============================================================
# Stage 2: Flask application
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Make project root available for Python imports
ENV PYTHONPATH=/app

# Port used by Render
ENV PORT=10000

# System dependencies required by FAISS / NumPy
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*


# ============================================================
# Python dependencies
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# ============================================================
# Copy complete project
# ============================================================

COPY . .


# ============================================================
# Copy React production build
# ============================================================

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist


# ============================================================
# Render
# ============================================================

EXPOSE 10000


# ============================================================
# Start Flask with Gunicorn
# ============================================================

CMD ["sh", "-c", "gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:$PORT app:app"]