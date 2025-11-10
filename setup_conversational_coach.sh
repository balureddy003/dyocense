#!/bin/bash

# AI Coach Conversational Upgrade - Quick Setup Script
# This script installs dependencies and configures the conversational AI coach

set -e  # Exit on error

echo "========================================"
echo "AI Coach Conversational Upgrade Setup"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements-dev.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /Users/balu/Projects/dyocense"
    exit 1
fi

echo "📦 Installing LangGraph and dependencies..."
pip install langgraph langchain-openai

echo ""
echo "✅ Dependencies installed successfully!"
echo ""

# Ask user which LLM provider to use
echo "🤖 Which LLM provider would you like to use?"
echo "1) Ollama (Free, runs locally - recommended for development)"
echo "2) OpenAI (Paid, cloud-hosted - recommended for production)"
echo "3) Azure OpenAI (Paid, enterprise)"
echo "4) Skip configuration (I'll do it manually)"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📥 Setting up Ollama..."
        
        # Check if Ollama is installed
        if command -v ollama &> /dev/null; then
            echo "✅ Ollama is already installed"
        else
            echo "❌ Ollama is not installed"
            echo ""
            echo "Please install Ollama first:"
            echo "  macOS: brew install ollama"
            echo "  Linux: curl -fsSL https://ollama.ai/install.sh | sh"
            echo "  Or visit: https://ollama.ai"
            echo ""
            read -p "Press Enter after installing Ollama to continue..."
        fi
        
        # Check if Ollama is running
        if curl -s http://localhost:11434/api/version &> /dev/null; then
            echo "✅ Ollama service is running"
        else
            echo "⚠️  Ollama service is not running"
            echo "   Starting Ollama in background..."
            nohup ollama serve > /dev/null 2>&1 &
            sleep 2
            
            if curl -s http://localhost:11434/api/version &> /dev/null; then
                echo "✅ Ollama service started"
            else
                echo "❌ Failed to start Ollama"
                echo "   Please start it manually: ollama serve"
                exit 1
            fi
        fi
        
        # Pull llama2 model
        echo "📥 Pulling llama2 model (this may take a few minutes)..."
        ollama pull llama2
        
        # Set environment variables
        echo ""
        echo "✅ Ollama configured successfully!"
        echo ""
        echo "Add these to your .env file or shell profile:"
        echo "export LLM_PROVIDER=ollama"
        echo "export OLLAMA_BASE_URL=http://localhost:11434"
        echo "export OLLAMA_MODEL=llama2"
        
        # Optionally add to .env
        if [ -f ".env" ]; then
            read -p "Add to .env file? (y/n): " add_env
            if [ "$add_env" = "y" ]; then
                echo "" >> .env
                echo "# AI Coach Configuration (added by setup script)" >> .env
                echo "LLM_PROVIDER=ollama" >> .env
                echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env
                echo "OLLAMA_MODEL=llama2" >> .env
                echo "✅ Added to .env file"
            fi
        fi
        ;;
    
    2)
        echo ""
        echo "🔑 Setting up OpenAI..."
        read -p "Enter your OpenAI API key: " api_key
        
        if [ -z "$api_key" ]; then
            echo "❌ No API key provided"
            exit 1
        fi
        
        echo "Select model:"
        echo "1) gpt-4 (slower, more expensive, smarter)"
        echo "2) gpt-3.5-turbo (faster, cheaper, good quality)"
        read -p "Enter choice (1-2): " model_choice
        
        if [ "$model_choice" = "1" ]; then
            model="gpt-4"
        else
            model="gpt-3.5-turbo"
        fi
        
        echo ""
        echo "✅ OpenAI configured!"
        echo ""
        echo "Add these to your .env file or shell profile:"
        echo "export LLM_PROVIDER=openai"
        echo "export OPENAI_API_KEY=$api_key"
        echo "export OPENAI_MODEL=$model"
        
        # Optionally add to .env
        if [ -f ".env" ]; then
            read -p "Add to .env file? (y/n): " add_env
            if [ "$add_env" = "y" ]; then
                echo "" >> .env
                echo "# AI Coach Configuration (added by setup script)" >> .env
                echo "LLM_PROVIDER=openai" >> .env
                echo "OPENAI_API_KEY=$api_key" >> .env
                echo "OPENAI_MODEL=$model" >> .env
                echo "✅ Added to .env file"
            fi
        fi
        ;;
    
    3)
        echo ""
        echo "☁️  Setting up Azure OpenAI..."
        read -p "Enter your Azure OpenAI API key: " api_key
        read -p "Enter your Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com): " endpoint
        read -p "Enter deployment name: " deployment
        
        echo ""
        echo "✅ Azure OpenAI configured!"
        echo ""
        echo "Add these to your .env file or shell profile:"
        echo "export LLM_PROVIDER=azure"
        echo "export AZURE_OPENAI_API_KEY=$api_key"
        echo "export AZURE_OPENAI_ENDPOINT=$endpoint"
        echo "export AZURE_OPENAI_DEPLOYMENT_NAME=$deployment"
        echo "export AZURE_OPENAI_API_VERSION=2024-02-15-preview"
        
        # Optionally add to .env
        if [ -f ".env" ]; then
            read -p "Add to .env file? (y/n): " add_env
            if [ "$add_env" = "y" ]; then
                echo "" >> .env
                echo "# AI Coach Configuration (added by setup script)" >> .env
                echo "LLM_PROVIDER=azure" >> .env
                echo "AZURE_OPENAI_API_KEY=$api_key" >> .env
                echo "AZURE_OPENAI_ENDPOINT=$endpoint" >> .env
                echo "AZURE_OPENAI_DEPLOYMENT_NAME=$deployment" >> .env
                echo "AZURE_OPENAI_API_VERSION=2024-02-15-preview" >> .env
                echo "✅ Added to .env file"
            fi
        fi
        ;;
    
    4)
        echo ""
        echo "⏭️  Skipping LLM configuration"
        echo ""
        echo "You can configure manually by setting these environment variables:"
        echo "  - LLM_PROVIDER (openai, azure, or ollama)"
        echo "  - OPENAI_API_KEY (for OpenAI)"
        echo "  - OPENAI_MODEL (for OpenAI)"
        echo ""
        echo "See AI_COACH_LLM_SETUP.md for details"
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd services/smb_gateway"
echo "   uvicorn main:app --reload --port 8000"
echo ""
echo "2. Start the frontend:"
echo "   cd apps/smb"
echo "   npm run dev"
echo ""
echo "3. Test the conversational coach:"
echo "   python scripts/test_conversational_coach.py"
echo ""
echo "4. Open browser and navigate to:"
echo "   http://localhost:3000"
echo ""
echo "📚 Documentation:"
echo "   - Setup guide: services/smb_gateway/CONVERSATIONAL_COACH_SETUP.md"
echo "   - LLM config: services/smb_gateway/AI_COACH_LLM_SETUP.md"
echo "   - Summary: AI_COACH_CONVERSATIONAL_UPGRADE.md"
echo ""
echo "🎉 Enjoy your new conversational AI Coach!"
