from fastapi import APIRouter
from .papers import router as papers_router
from .tasks import router as tasks_router
from .config import router as config_router

api_router = APIRouter()

api_router.include_router(papers_router)
api_router.include_router(tasks_router)
api_router.include_router(config_router)

__all__ = ["api_router"]
