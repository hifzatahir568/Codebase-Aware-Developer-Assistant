import bisect
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import numpy as np

from app.core.config import settings


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_path(p: str) -> str:
    return str(Path(p).expanduser().resolve())


def iter_source_files(project_path: str) -> List[str]:
    out = []
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in settings.ignore_folders]
        for name in files:
            ext = Path(name).suffix.lower()
            if ext not in settings.include_extensions:
                continue
            fp = os.path.join(root, name)
            try:
                if os.path.getsize(fp) <= settings.max_file_bytes:
                    out.append(fp)
            except OSError:
                continue
    return out


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk_text_with_line_ranges(text: str, chunk_size: int, overlap: int) -> List[Tuple[str, int, int]]:
    newline_positions = [i for i, ch in enumerate(text) if ch == "\n"]
    chunks = []
    start = 0
    n = len(text)

    def char_to_line(idx: int) -> int:
        return bisect.bisect_right(newline_positions, idx) + 1

    while start < n:
        end = min(start + chunk_size, n)
        snippet = text[start:end]
        if snippet.strip():
            chunks.append((snippet, char_to_line(start), char_to_line(max(start, end - 1))))
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def embedding_to_blob(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def blob_to_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def extractive_fallback_answer(question: str, context: str) -> str:
    tokens = [
        t
        for t in re.findall(r"[A-Za-z_]{3,}", question.lower())
        if t not in {"what", "does", "which", "function", "class"}
    ]
    lines = [ln.strip() for ln in context.splitlines() if ln.strip()]
    scored: List[Tuple[int, str]] = []
    for ln in lines:
        low = ln.lower()
        score = sum(1 for t in tokens if t in low)
        if score > 0:
            scored.append((score, ln))
    scored.sort(key=lambda x: x[0], reverse=True)

    top, seen = [], set()
    for _, ln in scored:
        if ln not in seen:
            seen.add(ln)
            top.append(ln)
        if len(top) == 4:
            break

    if top:
        joined = "\n".join(f"- {ln}" for ln in top)
        return f"Based on retrieved code context, the most relevant lines are:\n{joined}"
    return "I could not answer this reliably from the retrieved context. Try increasing `top_k` or re-indexing the project."
