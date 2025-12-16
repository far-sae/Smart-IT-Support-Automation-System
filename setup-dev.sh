#!/bin/bash

# Development environment setup script

echo "Setting up development environment..."
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

cd ..

# Frontend setup
echo ""
echo "📦 Setting up frontend..."
cd frontend

# Install dependencies
npm install
echo "✅ Frontend dependencies installed"

cd ..

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env with your credentials"
fi

# Create logs directory
mkdir -p logs
echo "✅ Logs directory created"

echo ""
echo "========================================="
echo "Development Setup Complete!"
echo "========================================="
echo ""
echo "To start development:"
echo ""
echo "Terminal 1 - PostgreSQL & Redis (via Docker):"
echo "  docker-compose up postgres redis"
echo ""
echo "Terminal 2 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Terminal 3 - Celery Worker:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  celery -A app.tasks.celery_app worker --loglevel=info"
echo ""
echo "Terminal 4 - Frontend:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "Then initialize database:"
echo "  python3 init_db.py"
echo ""
