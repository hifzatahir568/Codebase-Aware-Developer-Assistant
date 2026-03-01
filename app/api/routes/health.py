from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/")
def health_check():
    return {
        "status": "running",
        "app": settings.app_title,
        "embed_model": settings.embed_model_id,
        "llm_model": settings.llm_model_id,
        "db_path": settings.db_path,
    }
