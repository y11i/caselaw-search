from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class CaseDetail(BaseModel):
    id: str
    name: str
    citation: str
    court: str
    year: int
    facts: Optional[str]
    issue: Optional[str]
    holding: Optional[str]
    reasoning: Optional[str]
    full_text_url: str


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: str):
    """
    Retrieve detailed information about a specific case.
    """
    # TODO: Implement case retrieval from database
    raise HTTPException(status_code=404, detail="Case not found")
