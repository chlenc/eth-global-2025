#!/bin/bash

# Script for starting Funding Rate Arbitrage in Docker

set -e

echo "🚀 Starting Funding Rate Arbitrage in Docker..."

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Copy example.env to .env and fill in the required variables:"
    echo "cp example.env .env"
    exit 1
fi

# Create necessary directories
mkdir -p data logs

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose up --build -d

# Wait a bit for startup
echo "⏳ Waiting for services to start..."
sleep 10

# Show status
echo "📊 Container status:"
docker-compose ps

echo "✅ Application started!"
echo "📝 To view logs use: docker-compose logs -f funding-arbitrage"
echo "🛑 To stop use: docker-compose down"