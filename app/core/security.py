from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from app.core import config as config_module


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(api_key_header)) -> None:
    settings = config_module.settings
    if not settings.auth_enabled:
        return
    if not api_key or api_key not in settings.api_keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
