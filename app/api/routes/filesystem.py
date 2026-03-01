from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/filesystem", tags=["filesystem"])


@router.get("/dirs")
def list_directories(path: str | None = None):
    target = Path(path).expanduser().resolve() if path else Path.cwd().resolve()
    if not target.exists() or not target.is_dir():
        raise HTTPException(status_code=400, detail="Invalid directory path")

    try:
        dirs = sorted([p for p in target.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied for this directory")

    return {
        "path": str(target),
        "parent": str(target.parent) if target.parent != target else None,
        "directories": [{"name": d.name, "path": str(d)} for d in dirs],
    }
