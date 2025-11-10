import requests
from typing import List, Dict, Optional
from app.core.config import settings


class WebSearchService:
    """
    Service for web search using Tavily API.
    Used as fallback when vector search has low confidence results.
    """

    def __init__(self):
        self.api_key = settings.SEARCH_API_KEY
        self.api_url = "https://api.tavily.com/search"

    def search_legal_content(
        self,
        query: str,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search the web for legal content related to the query.

        Args:
            query: Legal search query
            max_results: Maximum number of results to return
            include_domains: Optional list of domains to prioritize
                           (e.g., ["courtlistener.com", "justia.com"])

        Returns:
            List of search results with title, url, content, score
        """
        try:
            # Default to legal domains if none specified
            if include_domains is None:
                include_domains = [
                    "courtlistener.com",
                    "justia.com",
                    "law.cornell.edu",
                    "supremecourt.gov",
                    "oyez.org"
                ]

            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",  # More comprehensive search
                "include_domains": include_domains,
                "include_answer": True  # Get AI-generated answer summary
            }

            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Format results
            results = []
            for result in data.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date")
                })

            # Include the AI-generated answer if available
            web_answer = data.get("answer")

            return {
                "results": results,
                "answer": web_answer,
                "query": query
            }

        except requests.exceptions.RequestException as e:
            print(f"Error performing web search: {e}")
            return {
                "results": [],
                "answer": None,
                "query": query,
                "error": str(e)
            }

    def search_specific_case(self, citation: str) -> Optional[Dict]:
        """
        Search for a specific case by citation.

        Args:
            citation: Legal citation (e.g., "410 U.S. 113")

        Returns:
            Best matching result or None
        """
        try:
            query = f'"{citation}" case law'
            search_result = self.search_legal_content(query, max_results=3)

            results = search_result.get("results", [])
            if results:
                # Return the highest scoring result
                return max(results, key=lambda x: x.get("score", 0))

            return None
        except Exception as e:
            print(f"Error searching for case {citation}: {e}")
            return None


# Singleton instance
web_search_service = WebSearchService()
