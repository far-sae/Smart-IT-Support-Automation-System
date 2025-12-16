#!/bin/bash

# Smart IT Support Automation System - Setup Script

set -e

echo "========================================="
echo "IT Support Automation System Setup"
echo "========================================="
echo ""

# Check for required tools
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/your-secret-key-change-in-production-min-32-chars/$SECRET_KEY/" .env
    rm .env.bak
    
    echo "✅ .env file created with random SECRET_KEY"
    echo "⚠️  Please edit .env and add your Azure AD credentials and other settings"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Create logs directory
mkdir -p logs
echo "✅ Logs directory created"
echo ""

# Build and start containers
echo "Building and starting containers..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Access the application:"
echo "  - Frontend: http://localhost:3000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - API: http://localhost:8000"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Azure AD and email credentials"
echo "  2. Restart services: docker-compose restart"
echo "  3. Create admin user (see README.md)"
echo "  4. Access the dashboard at http://localhost:3000"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo ""
