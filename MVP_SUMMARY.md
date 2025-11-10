# Legal AI MVP - Backend Implementation Summary

## Overview

Successfully implemented a **legal-oriented RAG (Retrieval-Augmented Generation) backend** for case law search. The MVP focuses on delivering accurate, well-cited legal answers using a specialized system prompt and hybrid search architecture.

## ✅ Completed Features

### 1. **Database Layer**
- ✅ SQLAlchemy models for `Case` and `CaseEmbedding`
- ✅ PostgreSQL schema with legal-specific fields (facts, issue, holding, reasoning)
- ✅ Automatic database initialization on startup
- ✅ Full session management with FastAPI dependency injection

**Location:** `backend/models/case.py`, `backend/app/db/`

### 2. **Core Services**

#### **Embedding Service** (`services/embedding_service.py`)
- Uses DeepSeek API (OpenAI-compatible) for embeddings
- Specialized `embed_legal_case()` method that combines:
  - Case name & citation
  - Legal issue
  - Holding (decision)
  - Facts & reasoning
- Optimized for semantic legal search

#### **Vector Search Service** (`services/vector_search_service.py`)
- Qdrant integration for semantic similarity search
- Cosine similarity for legal document matching
- Configurable score thresholds
- Metadata filtering (court, year, jurisdiction)
- Auto-creates collection on startup

#### **Web Search Service** (`services/web_search_service.py`)
- Tavily API integration for hybrid search
- Prioritizes legal domains:
  - courtlistener.com
  - justia.com
  - law.cornell.edu
  - supremecourt.gov
- Used as fallback when vector search confidence is low (<0.7)

#### **LLM Service with Legal System Prompt** (`services/llm_service.py`)
**🎯 This is the key "legal optimization" for the MVP!**

The system prompt includes:
- **Role Definition:** Expert legal research assistant for U.S. case law
- **IRAC Framework:** Issue, Rule, Application, Conclusion
- **Citation Requirements:**
  - Proper legal citation format (e.g., "Miranda v. Arizona, 384 U.S. 436 (1966)")
  - Attribution of principles to specific cases
  - Citation of most authoritative/recent precedent
- **Legal Reasoning:**
  - Distinguish majority, concurrences, dissents
  - Note overruled or limited cases
  - Identify split circuits or conflicting precedents
- **Jurisdiction Awareness:**
  - Binding vs. persuasive authority
  - Federal vs. state jurisdiction
  - Constitutional vs. statutory vs. common law
- **Professional Standards:**
  - Legal information, NOT legal advice
  - Recommend consulting licensed attorney
  - No outcome predictions
  - Acknowledge uncertainty

**Full system prompt:** See `backend/services/llm_service.py:11-66`

#### **Cache Service** (`services/cache_service.py`)
- Redis-based query caching
- 1-hour TTL for repeated queries
- Performance optimization
- Cache stats and health monitoring

#### **CourtListener Service** (`services/courtlistener_service.py`)
- Real case law data ingestion from CourtListener API
- Parses HTML/plain text opinions
- Extracts structured sections (facts, holding, reasoning)
- Auto-generates embeddings for each case
- Landmark case seeding function

### 3. **API Endpoints**

#### **POST /api/v1/search/** - RAG Pipeline
**Full implementation of:**
1. ✅ Cache check (Redis)
2. ✅ Query embedding generation
3. ✅ Vector search in Qdrant
4. ✅ Hybrid mode: Web search fallback if confidence < 0.7
5. ✅ LLM answer synthesis with legal system prompt
6. ✅ Citation extraction and formatting
7. ✅ Response caching

**Location:** `backend/app/api/endpoints/search.py`

#### **GET /api/v1/cases/{case_id}** - Case Details
- Retrieves full case information from database
- Returns structured legal fields
- Proper error handling

**Location:** `backend/app/api/endpoints/cases.py`

### 4. **Data Ingestion**

#### **Seeding Script** (`backend/seed_database.py`)
- Fetches landmark Supreme Court cases
- Queries include:
  - Miranda rights
  - Roe v. Wade
  - Brown v. Board of Education
  - Marbury v. Madison
  - Qualified immunity
  - Chevron deference
  - And more...
- Generates embeddings for each case
- Stores in PostgreSQL + Qdrant
- Progress tracking and error handling

**Usage:** `python seed_database.py --count 20`

### 5. **Testing Suite**

#### **Test Script** (`backend/test_legal_queries.py`)
Example queries:
- "What are Miranda rights?"
- "Explain qualified immunity for police officers"
- "What is the exclusionary rule?"
- "What did Brown v Board of Education establish?"

Tests verify:
- Proper legal citations
- IRAC reasoning framework
- Source relevance
- Answer accuracy

**Usage:** `python test_legal_queries.py`

## 🎯 Legal-Oriented Optimizations

### 1. **Domain-Specific System Prompt**
The legal system prompt (66 lines) ensures:
- Legal terminology accuracy
- Proper citation format
- IRAC reasoning structure
- Jurisdiction awareness
- Professional legal standards

### 2. **Hybrid RAG Architecture**
- **Corpus Search:** Vector similarity in Qdrant
- **Web Augmentation:** Tavily search when local corpus has gaps
- **Confidence Threshold:** 0.7 score triggers web fallback
- **Smart Prioritization:** On-point precedent > Supreme Court > Circuit > Recent

### 3. **Legal Document Embedding Strategy**
Combines multiple fields for semantic richness:
```python
Case Name + Citation + Issue + Holding + Facts + Reasoning
```
This creates embeddings optimized for legal semantic search.

### 4. **Citation Extraction & Verification**
LLM service tracks which cases are cited in answers and includes metadata.

## 📊 Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│  1. Check Redis Cache               │
└─────────────────────────────────────┘
    ↓ (miss)
┌─────────────────────────────────────┐
│  2. Embed Query (DeepSeek)          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Vector Search (Qdrant)          │
│     - Cosine similarity             │
│     - Score threshold: 0.5          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. Fetch Cases (PostgreSQL)        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  5. Check Confidence                │
│     if avg_score < 0.7 OR           │
│     results < 3                     │
└─────────────────────────────────────┘
    ↓ (low confidence)
┌─────────────────────────────────────┐
│  6. Web Search (Tavily)             │
│     - Legal domains only            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  7. LLM Synthesis (DeepSeek)        │
│     - Legal system prompt           │
│     - IRAC framework                │
│     - Citation generation           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  8. Cache Response (Redis)          │
│     - TTL: 1 hour                   │
└─────────────────────────────────────┘
    ↓
   Return Answer + Citations
```

## 🚀 Quick Start

### 1. Start Infrastructure
```bash
docker-compose up -d
```

### 2. Seed Database (First Time)
```bash
cd backend
source venv/bin/activate
python seed_database.py --count 20
```

This takes ~5-10 minutes to:
- Fetch 20 landmark Supreme Court cases
- Generate embeddings with DeepSeek
- Store in PostgreSQL + Qdrant

### 3. Start Backend
```bash
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

### 4. Test Queries
```bash
python test_legal_queries.py
```

Or use Swagger UI: http://localhost:8000/docs

## 📝 Example Query & Response

**Query:** "What are Miranda rights?"

**Expected Response:**
```
ANSWER:
Miranda rights, established in Miranda v. Arizona, 384 U.S. 436 (1966),
are constitutional protections that require law enforcement to inform
individuals in custody of their rights before interrogation.

[Issue] The legal issue is whether statements obtained during custodial
interrogation are admissible without prior warnings.

[Rule] The Fifth Amendment privilege against self-incrimination requires
that suspects be informed of:
1. The right to remain silent
2. That statements can be used against them
3. The right to an attorney
4. That an attorney will be appointed if they cannot afford one

[Application] In Miranda v. Arizona, 384 U.S. 436 (1966), the Supreme
Court held that these warnings are mandatory to protect against coercive
interrogation practices...

[Conclusion] Failure to provide Miranda warnings renders statements
inadmissible in criminal proceedings.

DISCLAIMER: This is legal information, not legal advice. Consult a
licensed attorney for specific legal matters.

SOURCES:
1. Miranda v. Arizona, 384 U.S. 436 (1966)
   - Supreme Court, 1966
   - Relevance: 0.923
```

## 📦 Tech Stack

- **Backend:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16
- **Vector DB:** Qdrant (latest)
- **Cache:** Redis 7
- **LLM:** DeepSeek (chat + embeddings)
- **Web Search:** Tavily API
- **Data Source:** CourtListener API

## 🔧 Configuration

All services use DeepSeek API:
- **Embeddings:** `deepseek-chat` model
- **Answer Generation:** `deepseek-chat` model with legal system prompt

**Environment Variables** (`.env`):
```
LLM_API_KEY=sk-...              # DeepSeek API key
SEARCH_API_KEY=tvly-...         # Tavily API key
COURTLISTENER_API_KEY=...       # CourtListener API key
```

## 📁 File Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app with DB init
│   ├── api/endpoints/
│   │   ├── search.py          # ✅ RAG pipeline implementation
│   │   └── cases.py           # ✅ Case detail endpoint
│   ├── core/config.py         # Settings & env vars
│   └── db/
│       └── database.py        # ✅ Session management
├── models/
│   └── case.py                # ✅ SQLAlchemy models
├── services/
│   ├── embedding_service.py   # ✅ DeepSeek embeddings
│   ├── vector_search_service.py  # ✅ Qdrant integration
│   ├── web_search_service.py  # ✅ Tavily integration
│   ├── llm_service.py         # ✅ Legal system prompt
│   ├── cache_service.py       # ✅ Redis caching
│   └── courtlistener_service.py  # ✅ Data ingestion
├── seed_database.py           # ✅ Seeding script
└── test_legal_queries.py      # ✅ Test suite
```

## ✨ Next Steps (Post-MVP)

1. **Frontend UI** - Build Next.js search interface
2. **More Cases** - Expand beyond 20 landmark cases
3. **Advanced Filters** - Court, year range, jurisdiction
4. **Citation Graph** - Visualize case relationships
5. **Case Summaries** - Auto-generate with LLM
6. **Authentication** - User accounts and history
7. **Monitoring** - Logging, metrics, error tracking

## 🎓 Legal System Prompt Highlights

The legal optimization is primarily in the **system prompt** (`services/llm_service.py`):

Key sections:
- **CORE RESPONSIBILITIES** - Legal analysis focus
- **CITATION REQUIREMENTS** - Proper legal citation format
- **LEGAL REASONING** - IRAC framework enforcement
- **JURISDICTION & SCOPE** - Binding vs. persuasive authority
- **LIMITATIONS** - Legal information vs. advice distinction
- **RESPONSE FORMAT** - Professional legal writing style

This prompt transforms a general LLM into a domain-specific legal research assistant.

## 📞 Support

Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
Qdrant Dashboard: http://localhost:6333/dashboard
