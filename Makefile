.PHONY: help setup start-services start-backend start-frontend start stop clean reset-db seed-db seed-landmark reseed-db

help:
	@echo "Legal AI - Available Commands:"
	@echo ""
	@echo "  make setup           - One-time setup (install dependencies, create env files)"
	@echo "  make start-services  - Start Docker services (PostgreSQL, Qdrant, Redis)"
	@echo "  make start-backend   - Start FastAPI backend server"
	@echo "  make start-frontend  - Start Next.js frontend server"
	@echo "  make start           - Start all services + backend + frontend"
	@echo "  make stop            - Stop all Docker services"
	@echo "  make clean           - Remove virtual env and node_modules"
	@echo ""
	@echo "Database commands:"
	@echo "  make reset-db        - Reset database (drops all tables and data)"
	@echo "  make seed-db         - Seed database with landmark cases (default: 20 cases)"
	@echo "  make seed-landmark   - Seed database with specific landmark cases"
	@echo "  make reseed-db       - Reset and seed database (convenience command)"
	@echo ""

setup:
	@echo "🚀 Setting up Legal AI project..."
	@echo ""
	@echo "📦 Installing backend dependencies..."
	cd backend && python -m venv venv && \
		(source venv/bin/activate && pip install -r requirements.txt)
	@echo ""
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo ""
	@echo "📝 Creating environment files..."
	@test -f backend/.env || cp backend/.env.example backend/.env
	@test -f frontend/.env.local || cp frontend/.env.local.example frontend/.env.local
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "⚠️  IMPORTANT: Edit backend/.env and add your API keys:"
	@echo "   - LLM_API_KEY"
	@echo "   - SEARCH_API_KEY (for web search)"
	@echo "   - COURTLISTENER_API_KEY"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit backend/.env with your API keys"
	@echo "  2. Run 'make start-services' to start Docker services"
	@echo "  3. Run 'make start-backend' and 'make start-frontend' in separate terminals"
	@echo "  OR run 'make start' to start everything together"

start-services:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services started:"
	@echo "   - PostgreSQL: localhost:5432"
	@echo "   - Qdrant: localhost:6333"
	@echo "   - Redis: localhost:6379"

start-backend:
	@echo "🚀 Starting FastAPI backend..."
	cd backend && source venv/bin/activate && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-frontend:
	@echo "🚀 Starting Next.js frontend..."
	cd frontend && npm run dev

start:
	@echo "🚀 Starting all services..."
	@echo ""
	@echo "This will start Docker services in the background."
	@echo "Backend and frontend will run in foreground (Ctrl+C to stop)."
	@echo ""
	@make start-services
	@echo ""
	@echo "⏳ Waiting 5 seconds for services to initialize..."
	@sleep 5
	@echo ""
	@echo "Starting backend and frontend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo ""
	@trap 'kill 0' EXIT; \
		(cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
		(cd frontend && npm run dev)

stop:
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped"

clean:
	@echo "🧹 Cleaning up..."
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -rf frontend/.next
	@echo "✅ Cleanup complete"

reset-db:
	@echo "🔄 Resetting database..."
	@echo "⚠️  WARNING: This will delete ALL data!"
	cd backend && source venv/bin/activate && python reset_database.py

seed-db:
	@echo "🌱 Seeding database with landmark cases..."
	cd backend && source venv/bin/activate && python seed_database.py --count 20

seed-landmark:
	@echo "🌱 Seeding database with specific landmark cases..."
	cd backend && source venv/bin/activate && python seed_landmark_cases.py

reseed-db: reset-db seed-db
	@echo "✅ Database reset and reseeded successfully!"
