from pathlib import Path
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.repositories import add_chunks, create_project, delete_project_chunks, get_project, list_chunks, update_last_indexed
from app.models.schemas import AskRequest, AskResponse, Citation, IndexProjectResponse, RegisterProjectRequest, RegisterProjectResponse
from app.services.indexing import blob_to_embedding, chunk_text_with_line_ranges, embedding_to_blob, iter_source_files, read_text, resolve_path, utc_now_iso
from app.services.llm import models
from app.services.qa import generate_answer

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_or_404(project_id: str):
    row = get_project(project_id)
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


@router.post("/register", response_model=RegisterProjectResponse)
def register_project(req: RegisterProjectRequest):
    project_path = resolve_path(req.project_path)
    if not req.project_path.strip():
        raise HTTPException(status_code=400, detail="Project path is required")
    if not project_path or not project_path.strip():
        raise HTTPException(status_code=400, detail="Project path invalid")

    import os

    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail="Project path invalid")

    project_id = str(uuid4())
    name = req.name.strip() if req.name else Path(project_path).name
    now = utc_now_iso()
    create_project(project_id, name, project_path, now)
    return RegisterProjectResponse(project_id=project_id, name=name, path=project_path)


@router.post("/{project_id}/index", response_model=IndexProjectResponse)
def index_project(project_id: str):
    project = get_project_or_404(project_id)
    files = iter_source_files(project["path"])

    embed_model = models.get_embed_model()
    chunks_indexed = 0
    scanned_files = len(files)

    rows = []
    for f in files:
        try:
            text = read_text(f)
        except OSError:
            continue

        file_chunks = chunk_text_with_line_ranges(text, settings.chunk_size, settings.chunk_overlap)
        if not file_chunks:
            continue

        embedding_vectors = embed_model.encode([c[0] for c in file_chunks], convert_to_numpy=True, normalize_embeddings=True)
        for idx, ((chunk_text, start, end), vec) in enumerate(zip(file_chunks, embedding_vectors)):
            rows.append((f, idx, start, end, chunk_text, embedding_to_blob(vec)))

    delete_project_chunks(project_id)
    if rows:
        chunks_indexed = add_chunks(project_id, rows)

    last_indexed = utc_now_iso()
    update_last_indexed(project_id, last_indexed)

    return {
        "project_id": project_id,
        "scanned_files": scanned_files,
        "changed_files": 0,
        "deleted_files": 0,
        "chunks_indexed": chunks_indexed,
        "last_indexed_at": last_indexed,
    }


@router.post("/{project_id}/ask", response_model=AskResponse)
def ask_project(project_id: str, req: AskRequest):
    project = get_project_or_404(project_id)
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    rows = list_chunks(project_id)
    if not rows:
        raise HTTPException(status_code=404, detail="No indexed chunks. Run /index first.")

    texts = [r["text"] for r in rows]
    vectors = np.vstack([blob_to_embedding(r["embedding"]) for r in rows])
    embed_model = models.get_embed_model()
    question_vec = embed_model.encode(question, convert_to_numpy=True, normalize_embeddings=True)
    if len(question_vec.shape) > 1:
        question_vec = question_vec[0]

    scores = vectors @ question_vec
    top_indices = np.argsort(scores)[::-1][: req.top_k]

    context_parts = []
    total_chars = 0
    citations = []

    for i in top_indices:
        r = rows[int(i)]
        chunk = texts[int(i)]
        if total_chars < req.max_context_chars:
            remaining = req.max_context_chars - total_chars
            take = chunk[:remaining]
            if take:
                context_parts.append(take)
                total_chars += len(take)

        citations.append(
            Citation(
                file=r["file_path"],
                start_line=r["start_line"],
                end_line=r["end_line"],
                score=float(scores[int(i)]),
            )
        )

    context = "\n\n".join(context_parts)
    answer = generate_answer(question, context, project["path"])
    return AskResponse(answer=answer, citations=citations)
