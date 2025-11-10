from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Case(Base):
    """
    Represents a legal case in the database.
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(String(500), nullable=False)
    citation = Column(String(200), unique=True, nullable=False, index=True)
    court = Column(String(200), nullable=False)
    year = Column(Integer, nullable=False, index=True)

    # Legal content fields
    facts = Column(Text, nullable=True)
    issue = Column(Text, nullable=True)
    holding = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    full_text = Column(Text, nullable=False)
    full_text_url = Column(String(500), nullable=True)

    # Metadata
    jurisdiction = Column(String(100), nullable=True)
    case_type = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    embeddings = relationship("CaseEmbedding", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Case(id={self.id}, citation='{self.citation}', name='{self.case_name}')>"


class CaseEmbedding(Base):
    """
    Stores vector embeddings for cases to enable semantic search.
    """
    __tablename__ = "case_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)

    # Embedding data
    embedding_model = Column(String(100), nullable=False)
    # Note: Actual vector stored in Qdrant, this tracks metadata
    # vector_id matches case_id (integer) in Qdrant
    vector_id = Column(Integer, nullable=False, unique=True, index=True)

    # Metadata about what was embedded
    content_type = Column(String(50), nullable=False)  # e.g., "full_text", "summary", "combined"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    case = relationship("Case", back_populates="embeddings")

    def __repr__(self):
        return f"<CaseEmbedding(id={self.id}, case_id={self.case_id}, model='{self.embedding_model}')>"


# Create indexes for common queries
Index('idx_case_court_year', Case.court, Case.year)
Index('idx_case_jurisdiction', Case.jurisdiction)
