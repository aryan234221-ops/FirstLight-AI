from __future__ import annotations

import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }

        for key in ("event", "workflow_id", "execution_id", "agent_name"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=True)


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.setLevel(logging.INFO)
    root.addHandler(handler)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id
        request.state.started_at = time.perf_counter()

        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        elapsed_ms = int((time.perf_counter() - request.state.started_at) * 1000)
        response.headers["x-request-id"] = request_id
        response.headers["x-latency-ms"] = str(elapsed_ms)
        return response
