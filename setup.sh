#!/bin/bash

echo "🚀 Setting up Legal AI project..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ All prerequisites found"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd ..
echo "✅ Backend setup complete"
echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend

echo "Installing Node dependencies..."
npm install

cd ..
echo "✅ Frontend setup complete"
echo ""

# Environment files
echo "📝 Creating environment files..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env"
else
    echo "⏭️  backend/.env already exists"
fi

if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo "✅ Created frontend/.env.local"
else
    echo "⏭️  frontend/.env.local already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "⚠️  IMPORTANT: Edit backend/.env and add your API keys:"
echo "   - LLM_API_KEY"
echo "   - SEARCH_API_KEY (for web search)"
echo "   - COURTLISTENER_API_KEY"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your API keys"
echo "  2. Run 'docker-compose up -d' to start services"
echo "  3. Run backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  4. Run frontend: cd frontend && npm run dev"
echo ""
echo "Or use the Makefile:"
echo "  make start-services  # Start Docker services"
echo "  make start-backend   # Start backend"
echo "  make start-frontend  # Start frontend"
