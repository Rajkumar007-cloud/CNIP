#!/bin/bash
# Setup script for Criminal Network Intelligence Platform

set -e

echo "=========================================="
echo "Criminal Network Intelligence Platform"
echo "Project PS26189 - SIH 2026"
echo "=========================================="

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "ERROR: $1 is not installed. Please install it first."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command docker
check_command docker-compose

# Create .env file if not exists
if [ ! -f backend/.env ]; then
    echo "Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    echo "Please edit backend/.env with your configuration"
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/fir_reports
mkdir -p data/surveillance
mkdir -p data/cdr
mkdir -p data/financial
mkdir -p ml/models
mkdir -p logs

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting core services (Neo4j, Redis)..."
docker-compose up -d neo4j redis

echo "Waiting for Neo4j to be healthy..."
sleep 10

echo "Starting backend..."
docker-compose up -d backend

echo "Waiting for backend to be ready..."
sleep 15

echo "Starting frontend..."
docker-compose up -d frontend

echo "=========================================="
echo "Platform started successfully!"
echo "=========================================="
echo ""
echo "Access points:"
echo "  Frontend Dashboard: http://localhost:5173"
echo "  Backend API:        http://localhost:8000"
echo "  API Documentation:  http://localhost:8000/docs"
echo "  Neo4j Browser:      http://localhost:7474"
echo "  Redis:              localhost:6379"
echo ""
echo "To generate synthetic data:"
echo "  docker-compose --profile init run --rm data-generator"
echo ""
echo "To process documents:"
echo "  docker-compose --profile init run --rm nlp-processor"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f [service_name]"
echo ""
echo "To stop:"
echo "  docker-compose down"
echo ""
echo "To stop and remove volumes:"
echo "  docker-compose down -v"