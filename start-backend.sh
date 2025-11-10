#!/bin/bash

echo "🚀 Starting FastAPI backend..."
echo ""

cd backend

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   ./setup.sh"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using default configuration."
    echo "   Copy .env.example to .env and add your API keys for full functionality."
    echo ""
fi

source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""
echo "Backend running at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
