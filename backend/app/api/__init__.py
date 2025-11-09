from fastapi import APIRouter
from app.api.endpoints import search, cases

router = APIRouter()

router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(cases.router, prefix="/cases", tags=["cases"])
