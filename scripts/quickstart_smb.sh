#!/bin/bash
# =====================================================================
# Dyocense SMB Quick Start Script
# =====================================================================
# Quickly deploy Dyocense in SMB-optimized mode
# Usage: ./scripts/quickstart_smb.sh
# =====================================================================

set -e

echo "🚀 Dyocense SMB Quick Start"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker installed${NC}"
echo -e "${GREEN}✓ Docker Compose installed${NC}"
echo ""

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.smb.example .env
    
    # Generate secure secrets
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -base64 32)
        JWT_SECRET=$(openssl rand -base64 32)
        POSTGRES_PASSWORD=$(openssl rand -base64 32)
        
        # Update .env with generated secrets
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
            sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|g" .env
            sed -i '' "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" .env
        else
            # Linux
            sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env
            sed -i "s|JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|g" .env
            sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" .env
        fi
        
        echo -e "${GREEN}✓ Generated secure secrets${NC}"
    else
        echo -e "${YELLOW}⚠ OpenSSL not found. Please update secrets in .env manually.${NC}"
    fi
else
    echo -e "${YELLOW}ℹ .env file already exists, skipping creation${NC}"
fi

echo ""

# Start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.smb.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check health
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Services are healthy!${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Services failed to start. Check logs with: docker-compose -f docker-compose.smb.yml logs${NC}"
    exit 1
fi

echo ""
echo "=============================="
echo -e "${GREEN}✅ Dyocense SMB is running!${NC}"
echo "=============================="
echo ""
echo "📍 Service URLs:"
echo "   - API: http://localhost:8001"
echo "   - API Docs: http://localhost:8001/api/docs"
echo "   - Health: http://localhost:8001/health"
echo "   - Status: http://localhost:8001/status"
echo ""
echo "📊 PostgreSQL:"
echo "   - Host: localhost:5432"
echo "   - Database: dyocense"
echo "   - User: dyocense"
echo ""
echo "🔧 Useful Commands:"
echo "   - View logs: docker-compose -f docker-compose.smb.yml logs -f"
echo "   - Stop: docker-compose -f docker-compose.smb.yml down"
echo "   - Restart: docker-compose -f docker-compose.smb.yml restart"
echo "   - Shell: docker exec -it dyocense-kernel bash"
echo ""
echo "📚 Documentation:"
echo "   - Deployment Guide: docs/SMB_DEPLOYMENT_GUIDE.md"
echo "   - Architecture: docs/architecture-smb-optimized.md"
echo "   - Status: docs/IMPLEMENTATION_STATUS.md"
echo "   - Gaps & Enhancements: docs/GAPS_AND_ENHANCEMENTS.md"
echo ""
echo -e "${GREEN}Happy building! 🎉${NC}"
