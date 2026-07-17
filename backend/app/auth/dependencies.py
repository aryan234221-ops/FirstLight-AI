from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status

from app.auth.rbac import collect_permissions
from app.auth.service import AuthService
from app.core.application import ApplicationContext


context = ApplicationContext()


def get_auth_service() -> AuthService:
    return context.auth_service


def get_current_user(request: Request) -> dict[str, object]:
    principal = getattr(request.state, "principal", None)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return principal


def require_permissions(*required: str) -> Callable[[dict[str, object]], dict[str, object]]:
    def _dependency(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
        roles = current_user.get("roles")
        role_list = [role for role in roles if isinstance(role, str)] if isinstance(roles, list) else []
        permissions = collect_permissions(role_list)
        missing = [perm for perm in required if perm not in permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(sorted(missing))}",
            )
        return current_user

    return _dependency
