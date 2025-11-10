# Legal AI - RAG-based Case Law Search

A domain-specific AI assistant for semantic search, summarization, and exploration of U.S. case law with hybrid RAG (local corpus + web search).

> **🚀 Quick Start**: See [QUICK_START.md](./QUICK_START.md) for simple setup and run commands.

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, TailwindCSS
- **Backend**: FastAPI (Python), PostgreSQL, Qdrant
- **LLM**: OpenAI GPT-5 / Anthropic Claude
- **Vector DB**: Qdrant
- **Cache**: Redis
- **Data Source**: CourtListener API

## Project Structure

```
caselaw-search/
├── frontend/             # Next.js application
│   ├── app/              # App router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and helpers
│   └── public/           # Static assets
│
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration
│   │   ├── db/           # Database setup
│   │   └── main.py       # FastAPI app
│   ├── models/           # Database models
│   ├── services/         # Business logic (RAG, embeddings, LLM)
│   ├── utils/            # Helper functions
│   └── requirements.txt
│
└── docker-compose.yml   # Services (Postgres, Qdrant, Redis)
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone and navigate to the project

```bash
cd caselaw-search
```

### 2. Start infrastructure services

```bash
docker-compose up -d
```

Kill any processes that are running at the ports beloe 
```
sudo lsof -i :<port>
sudo kill <pid>
```

This starts:
- PostgreSQL (port 5432)
- Qdrant vector DB (port 6333)
- Redis cache (port 6379)

### 3. Set up Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see backend/.env.example)
cp .env.example .env
# Edit .env and add your API keys

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 4. Set up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run the development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## MVP Backend - Getting Started

The MVP focuses on the backend with a **legal-oriented RAG pipeline**. Follow these steps:

### 1. Ensure Docker Services are Running

```bash
docker-compose up -d
```

### 2. Activate Backend Environment

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 3. Seed Database with Landmark Cases

This fetches ~20 Supreme Court cases from CourtListener and creates embeddings:

```bash
python seed_database.py --count 20
```

This will take a few minutes as it:
- Fetches cases from CourtListener API
- Generates embeddings using DeepSeek
- Stores cases in PostgreSQL
- Indexes embeddings in Qdrant

### 4. Start the Backend Server

```bash
uvicorn app.main:app --reload
```

### 5. Test Legal Queries

Run the test script to verify the RAG pipeline:

```bash
python test_legal_queries.py
```

Or test manually at: http://localhost:8000/docs

**Example Legal Queries:**
- "What are Miranda rights?"
- "Explain qualified immunity for police officers"
- "What is the exclusionary rule?"
- "What did Brown v Board of Education establish?"

### Key MVP Features

✅ **Legal-Oriented System Prompt** - Specialized for case law analysis using IRAC framework
✅ **Hybrid RAG** - Vector search with web fallback for low-confidence queries
✅ **Proper Citations** - Automatic legal citation formatting
✅ **CourtListener Integration** - Real landmark Supreme Court cases
✅ **Redis Caching** - Performance optimization for repeated queries
✅ **Semantic Search** - Qdrant vector database with DeepSeek embeddings

## API Endpoints

### Backend API (FastAPI)

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/v1/search/` - Semantic search with RAG
- `GET /api/v1/cases/{case_id}` - Get case details

API docs available at: http://localhost:8000/docs

## Development Workflow

### Backend Development

```bash
cd backend
source venv/bin/activate

# Run with hot reload
uvicorn app.main:app --reload

# Run tests
pytest

# Format code
black .
ruff check .
```

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

## Environment Variables

### Backend (.env)

```env
# LLM API Key
LLM_API_KEY=your_llm_key

# Web Search
SEARCH_API_KEY=your_search_key

# CourtListener
COURTLISTENER_API_KEY=your_courtlistener_key

# Database (if not using docker-compose defaults)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legalai

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## License

MIT
