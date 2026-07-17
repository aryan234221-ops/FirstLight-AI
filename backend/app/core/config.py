from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityConfig:
    jwt_secret: str
    jwt_algorithm: str
    access_token_ttl_seconds: int
    refresh_token_ttl_seconds: int


@dataclass(frozen=True)
class PlatformConfig:
    app_version: str
    security: SecurityConfig



def load_config() -> PlatformConfig:
    return PlatformConfig(
        app_version=os.getenv("FIRSTLIGHT_APP_VERSION", "2.0.0-enterprise"),
        security=SecurityConfig(
            jwt_secret=os.getenv("FIRSTLIGHT_JWT_SECRET", "firstlight-dev-secret-change-me"),
            jwt_algorithm="HS256",
            access_token_ttl_seconds=int(os.getenv("FIRSTLIGHT_ACCESS_TTL", "1800")),
            refresh_token_ttl_seconds=int(os.getenv("FIRSTLIGHT_REFRESH_TTL", "604800")),
        ),
    )
