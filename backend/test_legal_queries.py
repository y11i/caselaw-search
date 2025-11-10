#!/usr/bin/env python3
"""
Test script for Legal AI MVP backend.
Sends test legal queries to verify the RAG pipeline works correctly.

Usage:
    python test_legal_queries.py
"""

import requests
import json
from typing import List, Dict


API_BASE_URL = "http://localhost:8000/api/v1"


def test_search(query: str, mode: str = "hybrid") -> Dict:
    """
    Test the search endpoint with a legal query.

    Args:
        query: Legal question
        mode: Search mode ("hybrid" or "corpus_only")

    Returns:
        Response dict
    """
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"MODE: {mode}")
    print(f"{'='*80}\n")

    try:
        response = requests.post(
            f"{API_BASE_URL}/search/",
            json={
                "query": query,
                "mode": mode,
                "limit": 5
            },
            timeout=60  # Legal queries with LLM can take time
        )

        response.raise_for_status()
        result = response.json()

        # Print answer
        print("ANSWER:")
        print("-" * 80)
        print(result["answer"])
        print()

        # Print sources
        print("SOURCES:")
        print("-" * 80)
        for i, source in enumerate(result["sources"], 1):
            print(f"{i}. {source['case_name']}")
            print(f"   Citation: {source['citation']}")
            print(f"   Court: {source['court']}, Year: {source['year']}")
            print(f"   Relevance Score: {source['relevance_score']:.3f}")
            print(f"   Summary: {source['summary'][:100]}...")
            print()

        return result

    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Response: {e.response.json()}")
            except:
                print(f"Response: {e.response.text}")
        return {}


def test_case_detail(case_id: int) -> Dict:
    """
    Test the case detail endpoint.

    Args:
        case_id: Database ID of the case

    Returns:
        Case detail dict
    """
    print(f"\n{'='*80}")
    print(f"FETCHING CASE DETAIL: ID={case_id}")
    print(f"{'='*80}\n")

    try:
        response = requests.get(f"{API_BASE_URL}/cases/{case_id}")
        response.raise_for_status()
        case = response.json()

        print(f"Name: {case['name']}")
        print(f"Citation: {case['citation']}")
        print(f"Court: {case['court']}")
        print(f"Year: {case['year']}")
        print(f"\nHolding:")
        print(case.get('holding', 'N/A'))
        print()

        return case

    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return {}


def main():
    """Run test queries"""

    print("\n" + "="*80)
    print("LEGAL AI MVP - BACKEND TESTING")
    print("="*80)

    # Test legal queries
    test_queries = [
        "What are Miranda rights?",
        "Explain qualified immunity for police officers",
        "What is the exclusionary rule?",
        "What did Brown v Board of Education establish?",
        "Explain the right to counsel in criminal cases"
    ]

    print("\n📋 Running test queries...\n")

    results = []
    for query in test_queries:
        result = test_search(query, mode="hybrid")
        results.append(result)

        # Brief pause between queries
        import time
        time.sleep(2)

    # Test case detail endpoint if we have results
    if results and results[0].get("sources"):
        first_case_id = 1  # Assuming first case has ID 1
        test_case_detail(first_case_id)

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\n✓ All tests completed. Check the output above for results.")
    print("\n💡 Tips:")
    print("  - Answers should cite cases with proper legal citations")
    print("  - Check that sources are relevant to the query")
    print("  - Verify legal reasoning follows IRAC framework")
    print("  - Ensure no legal advice disclaimers are present")


if __name__ == "__main__":
    main()
