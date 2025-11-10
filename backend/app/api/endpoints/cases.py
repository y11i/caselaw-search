from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db import get_db
from models import Case

router = APIRouter()


class CaseDetail(BaseModel):
    id: int
    name: str
    citation: str
    court: str
    year: int
    facts: Optional[str]
    issue: Optional[str]
    holding: Optional[str]
    reasoning: Optional[str]
    full_text_url: Optional[str]
    jurisdiction: Optional[str]
    case_type: Optional[str]


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: int, db: Session = Depends(get_db)):
    """
    Retrieve detailed information about a specific case by ID.

    Args:
        case_id: Database ID of the case

    Returns:
        Detailed case information including facts, holding, reasoning, etc.
    """
    # Fetch case from database
    case = db.query(Case).filter(Case.id == case_id).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case with ID {case_id} not found"
        )

    return CaseDetail(
        id=case.id,
        name=case.case_name,
        citation=case.citation,
        court=case.court,
        year=case.year,
        facts=case.facts,
        issue=case.issue,
        holding=case.holding,
        reasoning=case.reasoning,
        full_text_url=case.full_text_url,
        jurisdiction=case.jurisdiction,
        case_type=case.case_type
    )
