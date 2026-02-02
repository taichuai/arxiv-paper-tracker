from fastapi import APIRouter
from .papers import router as papers_router
from .tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(papers_router)
api_router.include_router(tasks_router)

__all__ = ["api_router"]
