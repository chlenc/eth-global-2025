#!/bin/bash

# Script to stop Funding Rate Arbitrage

echo "🛑 Stopping Funding Rate Arbitrage..."

# Stop containers
docker compose down

echo "✅ Application stopped!"

# Show status
echo "📊 Container status:"
docker compose ps 