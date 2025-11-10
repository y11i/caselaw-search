# Quick Start Guide

## 🔧 One-Time Setup (Run Once)

### Option 1: Using the setup script (Recommended)
```bash
./setup.sh
```

### Option 2: Using Makefile
```bash
make setup
```

### Option 3: Manual setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd ..

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
cd ..
```

**After setup:**
- Edit `backend/.env` and add your API keys
- No need to edit `frontend/.env.local` unless changing API URL

---

## 🚀 Starting the Application (Every Time)

### Step 1: Start Docker Services (Required)
```bash
# Start PostgreSQL, Qdrant, and Redis
docker-compose up -d

# Or using make
make start-services
```

### Step 2: Start Backend (in terminal 1)
```bash
./start-backend.sh

# Or using make
make start-backend

# Or manually
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Start Frontend (in terminal 2)
```bash
./start-frontend.sh

# Or using make
make start-frontend

# Or manually
cd frontend
npm run dev
```

---

## 📍 Access URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## 🛑 Stopping the Application

### Stop backend and frontend
Press `Ctrl+C` in each terminal

### Stop Docker services
```bash
docker-compose down

# Or using make
make stop
```

---

## 📦 Summary

### Run Once (Setup):
```bash
./setup.sh                    # Install dependencies and create env files
# Edit backend/.env with API keys
```

### Run Every Time:
```bash
# Terminal 1: Start services
docker-compose up -d

# Terminal 2: Start backend
./start-backend.sh

# Terminal 3: Start frontend
./start-frontend.sh
```

### Alternative (using Makefile):
```bash
# One-time setup
make setup

# Every time
make start-services     # In terminal 1
make start-backend      # In terminal 2
make start-frontend     # In terminal 3
```

---

## ⚡ Pro Tips

1. **Check if ports are free** (if services fail to start):
   ```bash
   sudo lsof -i :5432   # PostgreSQL
   sudo lsof -i :6333   # Qdrant
   sudo lsof -i :6379   # Redis
   sudo lsof -i :8000   # Backend
   sudo lsof -i :3000   # Frontend

   # Kill process if needed
   sudo kill -9 <PID>
   ```

2. **View Docker service logs**:
   ```bash
   docker-compose logs -f
   ```

3. **Reset everything** (if something breaks):
   ```bash
   docker-compose down
   make clean
   make setup
   ```
