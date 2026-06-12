#!/bin/bash
# Script to build and push Mediqr Docker images to Docker Hub

# Stop on any error
set -e

# Default Docker Hub username if not provided as argument
DOCKER_USERNAME=${1:-"your_dockerhub_username"}

# Check if username is still the placeholder
if [ "$DOCKER_USERNAME" == "your_dockerhub_username" ]; then
    echo "Warning: Using placeholder username. You should pass your actual Docker Hub username."
    echo "Usage: ./scripts/docker_push.sh <your_dockerhub_username>"
    exit 1
fi

echo "=========================================================="
echo " MEDIQR - Docker Hub Push Script"
echo "=========================================================="

echo "[1/4] Logging in to Docker Hub..."
docker login

echo "[2/4] Building Backend Image..."
docker build -t ${DOCKER_USERNAME}/mediqr-backend:latest ./backend

echo "[3/4] Building Frontend Image..."
docker build -t ${DOCKER_USERNAME}/mediqr-frontend:latest ./frontend

echo "[4/4] Pushing images to Docker Hub..."
docker push ${DOCKER_USERNAME}/mediqr-backend:latest
docker push ${DOCKER_USERNAME}/mediqr-frontend:latest

echo "=========================================================="
echo "✅ Images successfully pushed to Docker Hub!"
echo "   Backend:  ${DOCKER_USERNAME}/mediqr-backend:latest"
echo "   Frontend: ${DOCKER_USERNAME}/mediqr-frontend:latest"
echo "=========================================================="
