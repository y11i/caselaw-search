from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional
from app.core.config import settings
from services.embedding_service import embedding_service


class VectorSearchService:
    """
    Service for semantic search using Qdrant vector database.
    Handles case law embeddings and similarity search.
    """

    def __init__(self):
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self.embedding_dim = embedding_service.embedding_dimension

        # Initialize collection if it doesn't exist
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE  # Cosine similarity for semantic search
                    )
                )
                print(f"Created Qdrant collection: {self.collection_name}")
            else:
                print(f"Qdrant collection already exists: {self.collection_name}")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            raise

    def add_case_embedding(
        self,
        case_id: int,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a case embedding to the vector database.

        Args:
            case_id: Database ID of the case
            embedding: Vector embedding of the case
            metadata: Additional metadata (citation, name, court, year, etc.)

        Returns:
            Vector ID (integer, same as case_id)
        """
        try:
            # Use case_id directly as the point ID (must be integer for Qdrant)
            vector_id = case_id

            # Prepare payload with metadata
            payload = metadata or {}
            payload["case_id"] = case_id

            # Create point
            point = PointStruct(
                id=vector_id,
                vector=embedding,
                payload=payload
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            return vector_id
        except Exception as e:
            print(f"Error adding case embedding: {e}")
            raise

    def search_similar_cases(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for cases similar to the query text.

        Args:
            query_text: Natural language legal query
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filters: Optional filters (e.g., court, year range)

        Returns:
            List of dicts with case_id, score, and metadata
        """
        try:
            # Generate embedding for query
            query_embedding = embedding_service.embed_text(query_text)

            # Prepare search filters if provided
            search_filter = None
            if filters:
                conditions = []
                if "court" in filters:
                    conditions.append(
                        FieldCondition(key="court", match=MatchValue(value=filters["court"]))
                    )
                if "min_year" in filters:
                    conditions.append(
                        FieldCondition(key="year", range={"gte": filters["min_year"]})
                    )
                if conditions:
                    search_filter = Filter(must=conditions)

            # Search Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )

            # Format results
            results = []
            for hit in search_results:
                results.append({
                    "case_id": hit.payload.get("case_id"),
                    "score": hit.score,
                    "citation": hit.payload.get("citation"),
                    "case_name": hit.payload.get("case_name"),
                    "court": hit.payload.get("court"),
                    "year": hit.payload.get("year"),
                    "vector_id": hit.id
                })

            return results
        except Exception as e:
            print(f"Error searching similar cases: {e}")
            raise

    def delete_case_embedding(self, case_id: int):
        """Delete a case embedding from the vector database"""
        try:
            # Use case_id directly as the point ID (integer)
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[case_id]
            )
        except Exception as e:
            print(f"Error deleting case embedding: {e}")
            raise

    def get_collection_info(self) -> Dict:
        """Get information about the collection (count, etc.)"""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            raise


# Singleton instance
vector_search_service = VectorSearchService()
