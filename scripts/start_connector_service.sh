#!/bin/bash
# Quick start script for connector service

set -e

echo "🔌 Setting up Dyocense Connector Service..."
echo ""

# Check if we're in the right directory
if [ ! -f "requirements-dev.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Generate encryption key if not set
if [ -z "$CONNECTOR_ENCRYPTION_KEY" ]; then
    echo "📝 Generating encryption key..."
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo ""
    echo "✅ Generated encryption key:"
    echo "   $ENCRYPTION_KEY"
    echo ""
    echo "⚠️  IMPORTANT: Save this key securely!"
    echo "   Add to your .env file:"
    echo "   CONNECTOR_ENCRYPTION_KEY=$ENCRYPTION_KEY"
    echo ""
    
    # Optionally add to .env
    read -p "Add to .env file now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if grep -q "CONNECTOR_ENCRYPTION_KEY=" .env 2>/dev/null; then
            echo "⚠️  CONNECTOR_ENCRYPTION_KEY already exists in .env"
        else
            echo "CONNECTOR_ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
            echo "✅ Added to .env"
        fi
    fi
    
    export CONNECTOR_ENCRYPTION_KEY=$ENCRYPTION_KEY
else
    echo "✅ Using existing CONNECTOR_ENCRYPTION_KEY"
fi

# Check dependencies
echo ""
echo "📦 Checking dependencies..."
if ! python3 -c "import cryptography" 2>/dev/null; then
    echo "Installing cryptography..."
    pip install cryptography
fi

if ! python3 -c "import httpx" 2>/dev/null; then
    echo "Installing httpx..."
    pip install httpx
fi

echo "✅ All dependencies installed"

# Check MongoDB
echo ""
echo "🗄️  Checking MongoDB..."
if ! curl -s http://localhost:27017 > /dev/null 2>&1; then
    echo "⚠️  MongoDB doesn't appear to be running on localhost:27017"
    echo "   You can start it with: brew services start mongodb-community"
    echo "   Or use Docker: docker run -d -p 27017:27017 mongo:latest"
else
    echo "✅ MongoDB is running"
fi

# Start the service
echo ""
echo "🚀 Starting Connector Service..."
echo "   Service will run on http://localhost:8009"
echo "   Press Ctrl+C to stop"
echo ""

MONGO_URI=${MONGO_URI:-mongodb://localhost:27017} \
CONNECTOR_ENCRYPTION_KEY=$CONNECTOR_ENCRYPTION_KEY \
python3 -m uvicorn services.connectors.main:app --reload --port 8009
