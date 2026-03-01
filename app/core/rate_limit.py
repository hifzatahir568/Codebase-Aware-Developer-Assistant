import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import config as config_module


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.window_seconds = 60
        self.max_requests = config_module.settings.rate_limit_per_minute
        self.hits: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if not config_module.settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if path in {"/", "/docs", "/openapi.json"} or path.startswith("/app"):
            return await call_next(request)

        now = time.time()
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{path}"
        queue = self.hits[key]

        while queue and now - queue[0] > self.window_seconds:
            queue.popleft()

        if len(queue) >= self.max_requests:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        queue.append(now)
        return await call_next(request)
