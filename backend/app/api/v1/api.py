from fastapi import APIRouter

from app.api.v1.endpoints import items, analysis

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(analysis.router, prefix="", tags=["analysis"])