#!/bin/bash

echo "🚀 Expense Manager - Quick Deploy Script"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your production values"
else
    echo "✅ .env file already exists"
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose down
docker-compose build
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Initialize database
echo "🗄️ Initializing database..."
curl -X POST http://localhost:5001/init_db \
  -H "Admin-Secret: admin-secret-key" \
  -H "Content-Type: application/json"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "🌐 WAN Layer (Users): http://localhost"
echo "🔐 VPN Layer (Admin): http://localhost:8501"
echo ""
echo "👥 Users can access from ANY network:"
echo "   📱 Mobile 4G/5G"
echo "   💻 Home WiFi" 
echo "   🏢 Office network"
echo "   ☕ Coffee shop WiFi"
echo ""
echo "🔐 Admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📖 For production deployment, see: production-setup.md"