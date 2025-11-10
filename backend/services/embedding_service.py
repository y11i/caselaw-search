from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class EmbeddingService:
    """
    Service for generating text embeddings using open-source models.
    Uses sentence-transformers with BGE (Beijing Academy of AI) model.
    Runs locally, no API key required.
    """

    def __init__(self):
        # Use BGE-small-en-v1.5 - excellent for retrieval, runs fast locally
        # Alternative options:
        # - "BAAI/bge-base-en-v1.5" (higher quality, slower)
        # - "all-MiniLM-L6-v2" (very fast, smaller)
        # - "Alibaba-NLP/gte-Qwen2-1.5B-instruct" (Qwen2-based if available)

        print("Loading embedding model (this may take a moment on first run)...")
        self.model_name = "BAAI/bge-small-en-v1.5"
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        print(f"✓ Loaded {self.model_name} (dimension: {self.embedding_dimension})")

    def embed_text(self, text: str, is_query: bool = True) -> List[float]:
        """
        Generate an embedding vector for a single text.

        Args:
            text: Input text to embed
            is_query: If True, uses query instruction; if False, uses document instruction

        Returns:
            List of floats representing the embedding vector
        """
        try:
            # For BGE models, use different instructions for queries vs documents
            if "bge" in self.model_name.lower():
                if is_query:
                    text = f"Represent this sentence for searching relevant passages: {text}"
                # Documents don't need a prefix for BGE

            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a batch.
        More efficient than calling embed_text multiple times.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Add BGE instruction prefix if using BGE model
            if "bge" in self.model_name.lower():
                texts = [f"Represent this sentence for searching relevant passages: {t}" for t in texts]

            embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise

    def embed_legal_case(self, case_data: dict) -> List[float]:
        """
        Generate an embedding for a legal case by combining key fields.
        Optimized for legal semantic search.

        Args:
            case_data: Dictionary with case information (name, facts, holding, etc.)

        Returns:
            Embedding vector for the combined case content
        """
        # Combine relevant fields for embedding
        # Prioritize: case name, issue, holding, facts, reasoning
        parts = []

        if case_data.get("case_name"):
            parts.append(f"Case: {case_data['case_name']}")

        if case_data.get("citation"):
            parts.append(f"Citation: {case_data['citation']}")

        if case_data.get("issue"):
            parts.append(f"Issue: {case_data['issue']}")

        if case_data.get("holding"):
            parts.append(f"Holding: {case_data['holding']}")

        if case_data.get("facts"):
            parts.append(f"Facts: {case_data['facts']}")

        if case_data.get("reasoning"):
            # Limit reasoning to avoid token limits
            reasoning = case_data['reasoning'][:2000]
            parts.append(f"Reasoning: {reasoning}")

        combined_text = "\n\n".join(parts)

        # This is a document (not a query), so set is_query=False
        return self.embed_text(combined_text, is_query=False)


# Singleton instance
embedding_service = EmbeddingService()
