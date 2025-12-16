#!/bin/bash

# Production deployment script

echo "🚀 Starting Production Deployment..."
echo ""

# Step 1: Check prerequisites
echo "1️⃣ Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Install Docker Compose first."
    exit 1
fi

# Step 2: Check environment variables
echo "2️⃣ Checking environment configuration..."
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Check critical variables
source .env
if [ "$DEBUG" = "True" ]; then
    echo "⚠️  WARNING: DEBUG=True in production! Set DEBUG=False"
    read -p "Continue anyway? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        exit 1
    fi
fi

# Step 3: Database initialization
echo "3️⃣ Initializing database..."
read -p "Have you configured the production database in .env? (y/N): " db_confirm
if [[ $db_confirm != [yY] ]]; then
    echo "❌ Configure DATABASE_URL in .env first."
    exit 1
fi

# Step 4: SSL certificates
echo "4️⃣ Checking SSL certificates..."
if [ ! -f nginx/ssl/fullchain.pem ]; then
    echo "⚠️  SSL certificates not found."
    read -p "Run setup_ssl.sh to get Let's Encrypt certificates? (y/N): " ssl_confirm
    if [[ $ssl_confirm == [yY] ]]; then
        chmod +x setup_ssl.sh
        ./setup_ssl.sh
    else
        echo "❌ SSL certificates required for production. Exiting."
        exit 1
    fi
fi

# Step 5: Build and start services
echo "5️⃣ Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "6️⃣ Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Step 7: Wait for services
echo "7️⃣ Waiting for services to be ready..."
sleep 10

# Step 8: Check health
echo "8️⃣ Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# Step 9: Initialize database
echo "9️⃣ Initializing database schema and admin user..."
python3 init_db.py

echo ""
echo "🎉 Production deployment complete!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "🌐 Access URLs:"
echo "   Frontend (HTTPS): https://support.yourcompany.com"
echo "   API Docs: https://support.yourcompany.com/api/docs"
echo "   Health Check: https://support.yourcompany.com/health"
echo ""
echo "👤 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!"
echo ""
echo "📝 View Logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🛑 Stop Services:"
echo "   docker-compose -f docker-compose.prod.yml down"
