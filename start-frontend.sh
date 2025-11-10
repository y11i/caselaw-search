#!/bin/bash

echo "🚀 Starting Next.js frontend..."
echo ""

cd frontend

if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found. Please run setup first:"
    echo "   ./setup.sh"
    exit 1
fi

if [ ! -f ".env.local" ]; then
    echo "⚠️  Warning: .env.local file not found. Using default configuration."
    echo ""
fi

echo "Frontend running at: http://localhost:3000"
echo ""

npm run dev
