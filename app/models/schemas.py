from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.config import settings


class RegisterProjectRequest(BaseModel):
    project_path: str
    name: Optional[str] = None


class RegisterProjectResponse(BaseModel):
    project_id: str
    name: str
    path: str


class IndexProjectResponse(BaseModel):
    project_id: str
    scanned_files: int
    changed_files: int
    deleted_files: int
    chunks_indexed: int
    last_indexed_at: str


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=settings.default_top_k, ge=1, le=settings.max_top_k)
    max_context_chars: int = Field(default=settings.default_max_context_chars, ge=500, le=30000)


class Citation(BaseModel):
    file: str
    start_line: int
    end_line: int
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
