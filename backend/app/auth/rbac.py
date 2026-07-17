from __future__ import annotations

from collections.abc import Iterable


ADMINISTRATOR = "administrator"
AI_ENGINEER = "ai_engineer"
DEVELOPER = "developer"
REVIEWER = "reviewer"
VIEWER = "viewer"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    ADMINISTRATOR: {
        "projects:read",
        "projects:write",
        "workflows:read",
        "workflows:write",
        "approvals:review",
        "knowledge:read",
        "knowledge:write",
        "history:read",
        "history:export",
        "chat:read",
        "chat:write",
        "dashboard:read",
        "settings:write",
        "users:manage",
    },
    AI_ENGINEER: {
        "projects:read",
        "projects:write",
        "workflows:read",
        "workflows:write",
        "knowledge:read",
        "knowledge:write",
        "history:read",
        "chat:read",
        "chat:write",
        "dashboard:read",
    },
    DEVELOPER: {
        "projects:read",
        "projects:write",
        "workflows:read",
        "workflows:write",
        "knowledge:read",
        "knowledge:write",
        "history:read",
        "chat:read",
        "chat:write",
        "dashboard:read",
    },
    REVIEWER: {
        "projects:read",
        "workflows:read",
        "approvals:review",
        "knowledge:read",
        "history:read",
        "chat:read",
        "dashboard:read",
    },
    VIEWER: {
        "projects:read",
        "workflows:read",
        "knowledge:read",
        "history:read",
        "chat:read",
        "dashboard:read",
    },
}


def collect_permissions(roles: Iterable[str]) -> set[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions |= ROLE_PERMISSIONS.get(role, set())
    return permissions
