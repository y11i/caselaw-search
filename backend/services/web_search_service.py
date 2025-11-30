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
        self.default_domains = [
            "courtlistener.com",
            "justia.com",
            "law.cornell.edu",
            "supremecourt.gov",
            "oyez.org"
        ]

    def search_legal_content(
        self,
        query: str,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None
    ) -> Dict:
        """
        Search the web for legal content related to the query.

        Args:
            query: Legal search query
            max_results: Maximum number of results to return
            include_domains: Optional list of domains to prioritize
                           (e.g., ["courtlistener.com", "justia.com"])

        Returns:
            Dict containing the Tavily answer (if available) and the raw result list
        """
        try:
            if not self.api_key:
                print("Tavily SEARCH_API_KEY is not configured; skipping web search fallback.")
                return {
                    "results": [],
                    "answer": None,
                    "query": query,
                    "error": "Missing SEARCH_API_KEY"
                }

            # Default to legal domains if none specified
            if include_domains is None:
                include_domains = self.default_domains.copy()

            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",  # Will fallback to basic if unavailable
                "include_domains": include_domains,
                "include_answer": True  # Get AI-generated answer summary
            }

            data = self._perform_search_with_fallback(payload)

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

    def _perform_search_with_fallback(self, payload: Dict) -> Dict:
        """
        Call Tavily API, retrying with basic depth if advanced is unavailable
        (e.g., when using a dev key).
        """
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            response = http_err.response
            if self._should_retry_with_basic_depth(response):
                print("Advanced Tavily search unavailable - falling back to basic depth.")
                basic_payload = payload.copy()
                basic_payload["search_depth"] = "basic"
                # include_answer is unavailable on basic depth
                basic_payload.pop("include_answer", None)
                # Dev plan returns at most 3 results reliably
                basic_payload["max_results"] = min(basic_payload.get("max_results", 5), 3)

                retry_response = requests.post(self.api_url, json=basic_payload, timeout=30)
                retry_response.raise_for_status()
                return retry_response.json()
            raise

    def _should_retry_with_basic_depth(self, response: Optional[requests.Response]) -> bool:
        if response is None:
            return False

        if response.status_code not in (400, 402, 403):
            return False

        try:
            error_data = response.json()
            message = error_data.get("error") or error_data.get("message") or str(error_data)
        except ValueError:
            message = response.text or ""

        message_lower = message.lower()
        keywords = ["advanced", "search_depth", "plan", "upgrade"]

        return any(keyword in message_lower for keyword in keywords)

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
