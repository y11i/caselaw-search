# Law AI Product Requirements Document (PRD)

## 🧭 Product Overview
A domain-specific AI assistant designed for legal professionals and students to semantically search, summarize, and explore case law. The MVP focuses on U.S. case law (federal + select state) using open data sources like CourtListener. It provides natural language Q&A and structured legal information (facts, issues, holdings, citations) similar to *Perplexity* but specialized for law. In addition to a local case corpus, the MVP supports Perplexity-style web RAG for general-purpose queries so results are not limited to downloaded cases.

---

## 🎯 Objectives
- Build an intuitive, accurate, and source-grounded legal research assistant.
- Enable users to query case law in natural language.
- Provide concise summaries (facts, issue, holding, reasoning) with verified citations.
- Use only open or user-provided data to minimize cost and licensing constraints.
- Support hybrid retrieval that augments the local corpus with trusted web sources for broader coverage.

---

## ⚙️ MVP Scope

### Core Features
1. **Semantic Legal Q&A (Perplexity-style)**
   - Users input a natural language query (e.g., “What cases define the exclusionary rule?”)
   - System retrieves relevant cases from a pre-indexed corpus.
   - LLM synthesizes a grounded answer citing specific cases and snippets.

2. **Case Summaries and Metadata Display**
   - Show case name, citation, court, year, and summary (facts, issue, holding, reasoning).
   - Provide link to full text via CourtListener or other open repository.

3. **Transparent Source Display**
   - Each response links to underlying sources with short text previews.
   - Optional “show reasoning” button reveals retrieval snippets.

4. **Vector-Based Retrieval (RAG)**
   - Use embeddings to perform semantic search over case summaries.
   - Store embeddings and metadata in a lightweight vector DB (e.g., Qdrant, Pinecone).

5. **Web Interface**
   - Clean, fast frontend built in Next.js with TailwindCSS.
   - Search bar, expandable answers, and citation links.
   - Minimalist layout optimized for text-heavy interaction.

6. **Caching and Query Efficiency**
   - Cache recent queries to reduce API calls and cost.
   - Implement simple rate-limiting.

7. **Hybrid RAG with Web Search (Perplexity-like)**
   - When local corpus recall or confidence is low, augment with live web search (e.g., Bing, Tavily, SerpAPI).
   - Fetch, extract, chunk, and embed top pages; re-rank with legal intent signals.
   - Synthesize answers using mixed sources; always cite URLs alongside case citations.
   - User toggle: “Legal corpus only” vs. “Hybrid (web + corpus)”.

---

## 🧠 Technical Architecture

**Frontend:** Next.js + TailwindCSS + Vercel hosting  
**Backend:** FastAPI or Node.js (TypeScript)  
**Database:** PostgreSQL for metadata + Qdrant (or Pinecone) for embeddings  
**LLM:** GPT-4 or Claude API (configurable)  
**Embeddings:** `text-embedding-3-large` (OpenAI) or `bge-large-en` (open-source)  
**Data Source:** CourtListener API (OpenJurist optional)  
**Web Search:** Bing Web Search or Tavily API (fallback: SerpAPI)  
**Content Extraction:** Readability/Trafilatura for clean text; HTML-to-text fallback  
**Hosting:**
- Backend on Render / Fly.io / local server for MVP
- Vector DB hosted (or self-hosted small instance)

**Pipeline (Hybrid RAG):**
1. User query → embedding search over local corpus → candidate cases + confidence score.
2. If low-confidence or user selects Hybrid: web search → fetch pages → extract → chunk → embed → re-rank with local results.
3. LLM synthesizes grounded answer with citations to cases and URLs; return with previews/snippets.

---

## 🧩 Data and Indexing Plan

### Source: CourtListener
- Access bulk data dumps of U.S. opinions.
- Parse and index:
  - Case name, citation, court, date
  - Summary (facts, issues, holdings)
  - Opinion text snippet (first 2–3 paragraphs)

### Embedding Strategy
- Generate embeddings for case summaries and/or key holdings.
- Store metadata with case IDs for retrieval.
- Optionally pre-summarize with LLM for faster queries.

### Scale Targets
- MVP dataset: 10k–50k cases (small subset)
- Later expansion: incremental ingestion of full federal + select state opinions

---

## 🧱 MVP Milestones

| Phase | Description | Deliverables | ETA |
|-------|--------------|---------------|-----|
| **1. Setup & Data Ingestion** | Pull CourtListener data, normalize schema, store locally | Basic dataset (JSON / Postgres) | Week 1–2 |
| **2. Embedding Pipeline** | Generate embeddings + store in Qdrant | Searchable index of 10k cases | Week 2–3 |
| **3. Backend API (FastAPI)** | Query → Retrieve → Generate answer via LLM | Working RAG API | Week 3–4 |
| **4. Frontend MVP** | Build search UI + results display | Next.js frontend + search bar + results | Week 5–6 |
| **5. Caching + Error Handling** | Cache frequent queries, handle empty results | Stable, cost-efficient backend | Week 6–7 |
| **6. Feedback & Testing** | Legal students beta-test for accuracy | Annotated feedback, UX notes | Week 8 |

---

## 🚀 Future Features (Post-MVP)

### 1. **Case Uploads (Local RAG Extension)**
- Users upload case PDFs/text files.
- System extracts and summarizes case content.
- Creates private embeddings for user-uploaded documents.

### 2. **Holding Extraction & Brief Generation**
- Auto-generate structured case briefs.
- Summarize facts, issues, holding, reasoning in standard legal format.

### 3. **Citation Network / Graph Explorer**
- Visualize case relationships by citations.
- Click nodes to navigate precedent chains.

### 4. **Advanced Filters & Jurisdiction Selector**
- Filter by court, year, topic, or jurisdiction.
- Support state/federal and specialized courts.

### 5. **User Accounts and Saved Searches**
- Allow users to save searches, notes, and bookmarked cases.

### 6. **Tiered Answers / Quality Levels**
- Offer “fast” vs. “boosted” answers (similar to Anycase.ai).
- Balances cost with depth of response.

### 7. **Community Feedback and Corrections**
- Allow users to flag incorrect citations or hallucinations.
- Feedback loop improves accuracy and trust.

---

## 📈 Metrics of Success
- **Accuracy:** % of AI responses that cite correct, verifiable cases.
- **Engagement:** Avg. queries per session and dwell time per result.
- **Reliability:** % of queries returning valid answers.
- **Cost Efficiency:** Average API cost per query.
- **Coverage:** % of queries answered with at least one credible source (local or web).

---

## ⚖️ Risks & Mitigations
| Risk | Mitigation |
|------|-------------|
| Data quality / missing cases | Use reliable open sources; refresh frequently |
| API cost scaling | Implement caching, batching, and usage tiers |
| Hallucinated citations | Always display verified sources; include links/snippets |
| Legal accuracy concerns | Add disclaimers; allow user feedback/corrections |
| Over-complex MVP | Start with Q&A + citations + summaries only |
| Web content reliability/licensing | Prefer reputable sources; respect robots/ToS; cache snapshots |
| Latency from live web retrieval | Parallelize search/fetch; cache results; stream partial answers |

---

## 🧩 Summary
The MVP delivers a legally focused AI assistant combining hybrid (local + web) RAG-based semantic search with grounded summaries and citations. The initial release targets law students, offering accurate, source-backed case insights. Post-MVP expansions will add personal uploads, citation graphing, and community validation — evolving toward a trusted, AI-powered legal research platform.

