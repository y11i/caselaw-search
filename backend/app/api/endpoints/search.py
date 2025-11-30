import re
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import get_db
from models import Case
from services import (
    cache_service,
    vector_search_service,
    web_search_service,
    llm_service
)

router = APIRouter()


YEAR_PATTERN = re.compile(r"\b(1[8-9]\d{2}|20\d{2})\b")
CASE_REFERENCE_PATTERN = re.compile(r"([A-Za-z][\w&.,' -]+ v\. [A-Za-z][\w&.,' -]+)", re.IGNORECASE)


def extract_years(text: str) -> List[int]:
    return [int(year) for year in YEAR_PATTERN.findall(text)]


def extract_case_reference(text: str) -> Optional[str]:
    match = CASE_REFERENCE_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def case_reference_in_sources(reference: str, sources: List[dict]) -> bool:
    normalized_reference = reference.lower()

    def normalize_name(name: str) -> str:
        return name.lower().replace("co.", "company").replace("corp.", "corporation")

    for source in sources:
        case_name = source.get("case_name", "")
        citation = source.get("citation", "")
        if normalized_reference in case_name.lower() or normalized_reference in citation.lower():
            return True
        if normalize_name(reference) in normalize_name(case_name):
            return True
    return False


class SearchQuery(BaseModel):
    query: str
    mode: str = "hybrid"  # "corpus_only" or "hybrid"
    limit: int = 10


class SearchResult(BaseModel):
    case_name: str
    citation: str
    court: str
    year: int
    summary: str
    relevance_score: float
    url: str


class SearchResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    mode: str


@router.post("/", response_model=SearchResponse)
async def search_cases(query: SearchQuery, db: Session = Depends(get_db)):
    """
    Semantic search over case law corpus with optional web augmentation.

    RAG Pipeline:
    1. Check cache for recent identical queries
    2. Embed query and search vector database
    3. If hybrid mode and low confidence, augment with web search
    4. Generate legal answer using LLM with case citations
    5. Cache and return response
    """
    try:
        # Step 1: Check cache
        cached_response = cache_service.get_cached_response(query.query, query.mode)
        if cached_response:
            print(f"Cache hit for query: {query.query[:50]}...")
            return SearchResponse(**cached_response)

        # Step 2: Vector search for similar cases
        vector_results = vector_search_service.search_similar_cases(
            query_text=query.query,
            limit=query.limit,
            score_threshold=0.5
        )

        # Fetch full case data from database
        case_sources = []
        for result in vector_results:
            case_id = result.get("case_id")
            if case_id:
                case = db.query(Case).filter(Case.id == case_id).first()
                if case:
                    case_sources.append({
                        "case_id": case.id,
                        "case_name": case.case_name,
                        "citation": case.citation,
                        "court": case.court,
                        "year": case.year,
                        "facts": case.facts,
                        "holding": case.holding,
                        "reasoning": case.reasoning,
                        "score": result.get("score", 0.0),
                        "url": case.full_text_url or f"/api/v1/cases/{case.id}"
                    })

        # Step 3: Determine if we need web augmentation
        web_sources = None
        use_web_search = False
        query_years = extract_years(query.query)
        requested_year = max(query_years) if query_years else None
        latest_case_year = max((c.get("year") or 0) for c in case_sources) if case_sources else 0
        recency_gap = requested_year and requested_year > latest_case_year
        case_reference = extract_case_reference(query.query)
        reference_found = case_reference and case_reference_in_sources(case_reference, case_sources)

        if query.mode == "hybrid":
            # Check if vector search has low confidence
            avg_score = sum(c.get("score", 0) for c in case_sources) / len(case_sources) if case_sources else 0

            # Reduced threshold from 0.7 to 0.5 - BGE embeddings typically score lower
            # Only use web search if we have very few results or very low confidence
            trigger_reasons = []
            if avg_score < 0.5:
                trigger_reasons.append(f"Low confidence ({avg_score:.2f})")
            if len(case_sources) < 2:
                trigger_reasons.append("Fewer than 2 corpus matches")
            if recency_gap:
                trigger_reasons.append(f"Query references {requested_year}, latest corpus year {latest_case_year}")
            if case_reference and not reference_found:
                trigger_reasons.append(f"Case '{case_reference}' missing from corpus")

            if trigger_reasons:
                print("; ".join(trigger_reasons) + " - using web search augmentation")
                use_web_search = True
                web_result = web_search_service.search_legal_content(query.query, max_results=5)
                web_sources = web_result.get("results", [])
            else:
                print(f"Confidence: {avg_score:.2f} - using corpus only")

        # Step 4: Generate answer with LLM
        if not case_sources and not web_sources:
            raise HTTPException(
                status_code=404,
                detail="No relevant cases found. Try a different query or check if the database has been seeded with cases."
            )

        llm_result = llm_service.generate_legal_answer(
            query=query.query,
            case_sources=case_sources,
            web_sources=web_sources if use_web_search else None
        )

        answer = llm_result["answer"]

        # Step 5: Format sources for response
        sources = []
        for case in case_sources:
            # Use LLM to generate a brief summary if needed
            summary = case.get("holding", "")[:200] if case.get("holding") else "Summary not available"

            sources.append({
                "case_name": case["case_name"],
                "citation": case["citation"],
                "court": case["court"],
                "year": case["year"],
                "summary": summary,
                "relevance_score": case["score"],
                "url": case["url"]
            })

        response_data = {
            "answer": answer,
            "sources": sources,
            "mode": query.mode
        }

        # Step 6: Cache the response
        cache_service.cache_response(query.query, response_data, query.mode)

        return SearchResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
