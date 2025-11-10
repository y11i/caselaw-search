import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from models import Case, CaseEmbedding
from services.embedding_service import embedding_service
from services.vector_search_service import vector_search_service
from bs4 import BeautifulSoup
import time


class CourtListenerService:
    """
    Service for ingesting case law data from CourtListener API.
    Fetches, parses, and stores legal cases with embeddings.
    """

    def __init__(self):
        self.api_key = settings.COURTLISTENER_API_KEY
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        self.headers = {
            "Authorization": f"Token {self.api_key}"
        }

    def search_cases(
        self,
        query: str,
        court: Optional[str] = None,
        min_year: Optional[int] = None,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for cases using CourtListener API v4.
        Uses the /opinions/ endpoint with filtering.

        Args:
            query: Search query
            court: Optional court filter (e.g., "scotus" for Supreme Court)
            min_year: Optional minimum year filter
            max_results: Maximum number of results

        Returns:
            List of opinion dictionaries from API
        """
        try:
            # v4 API uses direct resource endpoints
            endpoint = f"{self.base_url}/opinions/"

            params = {
                "search": query,  # v4 uses 'search' parameter
                "page_size": min(max_results, 10),
            }

            # v4 uses nested field filtering with double underscores
            if court:
                params["cluster__docket__court"] = court
            if min_year:
                params["cluster__date_filed__gte"] = f"{min_year}-01-01"

            print(f"  Querying API: {params.get('search', '')}")
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])
            print(f"  → Found {len(results)} results")
            return results

        except Exception as e:
            print(f"Error searching CourtListener: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"API Error: {error_data}")
                except:
                    print(f"Status: {e.response.status_code}")
            return []

    def get_opinion_by_id(self, opinion_id: int) -> Optional[Dict]:
        """
        Fetch a specific opinion by its CourtListener ID.

        Args:
            opinion_id: CourtListener opinion ID

        Returns:
            Opinion data dict or None
        """
        try:
            endpoint = f"{self.base_url}/opinions/{opinion_id}/"

            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"  ⚠ Opinion {opinion_id} is restricted (403 Forbidden)")
            else:
                print(f"  ✗ HTTP error fetching opinion {opinion_id}: {e}")
            return None
        except Exception as e:
            print(f"  ✗ Error fetching opinion {opinion_id}: {e}")
            return None

    def parse_case_data(self, opinion_data: Dict) -> Dict:
        """
        Parse CourtListener opinion data into our case format.

        Args:
            opinion_data: Raw opinion data from CourtListener API

        Returns:
            Parsed case data dict
        """
        # Debug: Check if opinion_data is actually a dict
        if not isinstance(opinion_data, dict):
            print(f"ERROR: opinion_data is not a dict, it's a {type(opinion_data)}")
            print(f"Content: {opinion_data}")
            raise ValueError(f"Expected dict, got {type(opinion_data)}")

        # Extract cluster data (contains case metadata)
        # Note: cluster might be a URL string that needs to be fetched
        cluster_data = opinion_data.get("cluster", {})

        # If cluster is a URL string, fetch it
        if isinstance(cluster_data, str) and cluster_data.startswith("http"):
            print(f"  Fetching cluster data from URL: {cluster_data[:80]}...")
            try:
                response = requests.get(cluster_data, headers=self.headers, timeout=30)
                response.raise_for_status()
                cluster = response.json()
                print(f"  ✓ Fetched cluster: {cluster.get('case_name', 'Unknown')}")
            except Exception as e:
                print(f"  ✗ Error fetching cluster: {e}")
                cluster = {}
        else:
            cluster = cluster_data if isinstance(cluster_data, dict) else {}

        # Parse HTML content to extract text
        html_content = opinion_data.get("html_with_citations", "") or opinion_data.get("html", "")
        plain_text = opinion_data.get("plain_text", "")

        # Use plain text if available, otherwise parse HTML
        if plain_text:
            full_text = plain_text
        elif html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            full_text = soup.get_text(separator="\n", strip=True)
        else:
            full_text = ""

        # Handle docket which might also be a URL
        docket_data = cluster.get("docket", {})
        if isinstance(docket_data, str):
            # Docket is a URL, for now just infer from citation
            # If citation contains "U.S." it's likely Supreme Court
            citations = cluster.get("citations", [])
            if citations and isinstance(citations, list) and len(citations) > 0:
                reporter = citations[0].get("reporter", "")
                if "U.S." in reporter:
                    court_info = "Supreme Court of the United States"
                else:
                    court_info = "Federal Court"
            else:
                court_info = "Unknown Court"
        elif isinstance(docket_data, dict):
            court_info = docket_data.get("court", "Unknown Court")
        else:
            court_info = "Unknown Court"

        # Extract and format citation
        citation_str = ""
        citations = cluster.get("citations", [])
        if citations and isinstance(citations, list) and len(citations) > 0:
            # Get the first citation (usually the primary one)
            first_citation = citations[0]
            if isinstance(first_citation, dict):
                volume = first_citation.get("volume", "")
                reporter = first_citation.get("reporter", "")
                page = first_citation.get("page", "")
                citation_str = f"{volume} {reporter} {page}".strip()

        # Fallback to citation_string if available
        if not citation_str:
            citation_str = cluster.get("citation_string", "")

        # Build case data
        case_data = {
            "case_name": cluster.get("case_name", "Unknown Case"),
            "citation": citation_str,
            "court": court_info,
            "year": cluster.get("date_filed", "")[:4] if cluster.get("date_filed") else None,
            "full_text": full_text[:50000],  # Limit text length
            "full_text_url": f"https://www.courtlistener.com{cluster.get('absolute_url', '')}",
            "jurisdiction": court_info,
            "case_type": opinion_data.get("type", "")
        }

        # Try to extract structured sections (this is simplified - real extraction would be more complex)
        case_data["facts"] = self._extract_section(full_text, ["FACTS", "BACKGROUND"])
        case_data["issue"] = self._extract_section(full_text, ["ISSUE", "QUESTION"])
        case_data["holding"] = self._extract_section(full_text, ["HOLDING", "DECISION", "CONCLUSION"])
        case_data["reasoning"] = self._extract_section(full_text, ["REASONING", "ANALYSIS", "DISCUSSION"])

        return case_data

    def _extract_section(self, text: str, section_markers: List[str]) -> Optional[str]:
        """
        Simple heuristic to extract a section from case text.
        This is a basic implementation - could be improved with NLP.
        """
        text_upper = text.upper()

        for marker in section_markers:
            if marker in text_upper:
                start_idx = text_upper.find(marker)
                # Get next 1000 characters after the marker
                section_text = text[start_idx:start_idx + 1000]
                return section_text.strip()

        return None

    def ingest_case(self, opinion_data: Dict, db: Session) -> Optional[Case]:
        """
        Ingest a single case into the database with embeddings.

        Args:
            opinion_data: CourtListener opinion data
            db: Database session

        Returns:
            Created Case object or None if failed
        """
        try:
            # Parse case data
            case_data = self.parse_case_data(opinion_data)

            # Validate required fields
            if not case_data.get("citation"):
                # Try to create a basic citation from case name
                case_name = case_data.get('case_name', '')
                year = case_data.get('year', '')
                if case_name:
                    case_data["citation"] = f"{case_name} ({year})" if year else case_name
                    print(f"  ⚠ No formal citation, using: {case_data['citation']}")
                else:
                    print(f"  ✗ Skipping case - no citation or case name available")
                    return None

            if not case_data.get("full_text"):
                print(f"  ✗ Skipping case without full text: {case_data['citation']}")
                return None

            # Check if case already exists (by citation)
            existing_case = db.query(Case).filter(Case.citation == case_data["citation"]).first()
            if existing_case:
                print(f"Case already exists: {case_data['citation']}")
                return existing_case

            # Create case in database
            case = Case(
                case_name=case_data["case_name"],
                citation=case_data["citation"],
                court=case_data["court"],
                year=int(case_data["year"]) if case_data["year"] else None,
                facts=case_data["facts"],
                issue=case_data["issue"],
                holding=case_data["holding"],
                reasoning=case_data["reasoning"],
                full_text=case_data["full_text"],
                full_text_url=case_data["full_text_url"],
                jurisdiction=case_data["jurisdiction"],
                case_type=case_data["case_type"]
            )

            db.add(case)
            db.commit()
            db.refresh(case)

            print(f"Ingested case: {case.citation}")

            # Generate and store embedding
            embedding_vector = embedding_service.embed_legal_case(case_data)

            # Store in Qdrant
            vector_id = vector_search_service.add_case_embedding(
                case_id=case.id,
                embedding=embedding_vector,
                metadata={
                    "case_name": case.case_name,
                    "citation": case.citation,
                    "court": case.court,
                    "year": case.year
                }
            )

            # Track embedding in database
            case_embedding = CaseEmbedding(
                case_id=case.id,
                embedding_model=embedding_service.model_name,
                vector_id=vector_id,
                content_type="combined"
            )

            db.add(case_embedding)
            db.commit()

            print(f"Created embedding for case: {case.citation}")

            return case

        except Exception as e:
            print(f"Error ingesting case: {e}")
            db.rollback()
            return None

    def ingest_landmark_cases(self, db: Session, count: int = 20) -> List[Case]:
        """
        Ingest landmark Supreme Court cases for MVP seed data.

        Args:
            db: Database session
            count: Number of cases to ingest

        Returns:
            List of ingested Case objects
        """
        # Search for important Supreme Court cases
        landmark_queries = [
            "miranda rights",
            "palsgraf v long island railroad",
            "roe wade abortion",
            "brown board education",
            "marbury madison judicial review",
            "held v montana",
            "hawkins v mcgee",
            "terry v ohio",
            "qualified immunity",
            "chevron deference",
            "pennoyer v. neff",
            "international shoe company",
            "wickard v filburn"
        ]

        ingested_cases = []

        for query in landmark_queries:
            if len(ingested_cases) >= count:
                break

            print(f"Searching for cases: {query}")
            results = self.search_cases(query, court="scotus", max_results=2)

            for result in results:
                if len(ingested_cases) >= count:
                    break

                # Get full opinion data
                opinion_id = result.get("id")
                if opinion_id:
                    # Check if we already processed this opinion ID
                    if any(case.id == opinion_id for case in ingested_cases):
                        print(f"  ⊘ Opinion {opinion_id} already processed, skipping")
                        continue

                    print(f"  Fetching opinion ID: {opinion_id}")
                    opinion_data = self.get_opinion_by_id(opinion_id)
                    if opinion_data:
                        case = self.ingest_case(opinion_data, db)
                        if case:
                            # Only add to list if it's a new case (not "already exists")
                            if case not in ingested_cases:
                                ingested_cases.append(case)
                                print(f"  ✓ Successfully ingested: {case.citation}")

                    # Rate limiting - be nice to the API
                    time.sleep(0.5)  # Reduced from 1s to speed things up

        print(f"Ingested {len(ingested_cases)} landmark cases")
        return ingested_cases


# Singleton instance
courtlistener_service = CourtListenerService()
