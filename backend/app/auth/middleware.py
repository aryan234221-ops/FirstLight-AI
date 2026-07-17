from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.service import AuthService


class AuthContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service: AuthService) -> None:
        super().__init__(app)
        self._auth_service = auth_service

    async def dispatch(self, request: Request, call_next):
        request.state.principal = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token:
                try:
                    payload = self._auth_service.parse_access_token(token)
                except Exception:
                    payload = None
                request.state.principal = payload

        return await call_next(request)
