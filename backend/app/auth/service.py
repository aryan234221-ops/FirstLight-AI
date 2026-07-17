from __future__ import annotations

import bcrypt
from datetime import datetime, timezone

from app.auth import jwt_utils
from app.auth.rbac import AI_ENGINEER, ADMINISTRATOR
from app.core.config import PlatformConfig
from app.db.models import RefreshTokenModel, RoleModel, UserModel, UserRoleModel
from app.repositories.sql_repositories import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository, config: PlatformConfig) -> None:
        self._repository = repository
        self._config = config

    @staticmethod
    def hash_password(password: str) -> str:
        encoded = password.encode("utf-8")
        return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    def bootstrap_defaults(self) -> None:
        roles = [
            (ADMINISTRATOR, "Platform administrator"),
            (AI_ENGINEER, "AI engineer"),
            ("developer", "Application developer"),
            ("reviewer", "Workflow reviewer"),
            ("viewer", "Read-only viewer"),
        ]

        for name, description in roles:
            self._repository.ensure_role(name, description)

        admin = self._repository.get_user_by_username("admin")
        if admin is None:
            admin = UserModel(
                username="admin",
                email="admin@firstlight.local",
                password_hash=self.hash_password("ChangeMeNow123!"),
                is_active=True,
            )
            self._repository.create_user(admin)
            self._repository.assign_role(admin.id, ADMINISTRATOR)

    def authenticate(self, username: str, password: str) -> tuple[str, str, dict[str, object]]:
        user = self._repository.get_user_by_username(username)
        if user is None or not user.is_active:
            raise ValueError("Invalid username or password")
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid username or password")

        roles = self._repository.get_user_role_names(user.id)
        access_payload = jwt_utils.build_access_token_payload(user.id, user.username, roles, self._config.security)
        refresh_payload = jwt_utils.build_refresh_token_payload(user.id, self._config.security)
        access_token = jwt_utils.encode_token(access_payload, self._config.security.jwt_secret)
        refresh_token = jwt_utils.encode_token(refresh_payload, self._config.security.jwt_secret)

        self._repository.create_refresh_token(
            RefreshTokenModel(
                user_id=user.id,
                token_hash=jwt_utils.token_fingerprint(refresh_token),
                expires_at=datetime.fromtimestamp(float(refresh_payload["exp"]), tz=timezone.utc),
                revoked=False,
            )
        )

        return access_token, refresh_token, {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": roles,
        }

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        payload = jwt_utils.decode_token(refresh_token, self._config.security.jwt_secret)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        token_hash = jwt_utils.token_fingerprint(refresh_token)
        stored = self._repository.get_refresh_token_by_hash(token_hash)
        if stored is None or stored.revoked:
            raise ValueError("Refresh token invalid")

        user_id = str(payload.get("sub", ""))
        user = self._repository.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        roles = self._repository.get_user_role_names(user.id)
        access_payload = jwt_utils.build_access_token_payload(user.id, user.username, roles, self._config.security)
        new_access = jwt_utils.encode_token(access_payload, self._config.security.jwt_secret)

        new_refresh_payload = jwt_utils.build_refresh_token_payload(user.id, self._config.security)
        new_refresh = jwt_utils.encode_token(new_refresh_payload, self._config.security.jwt_secret)

        self._repository.revoke_refresh_token(stored.id)
        self._repository.create_refresh_token(
            RefreshTokenModel(
                user_id=user.id,
                token_hash=jwt_utils.token_fingerprint(new_refresh),
                expires_at=datetime.fromtimestamp(float(new_refresh_payload["exp"]), tz=timezone.utc),
                revoked=False,
            )
        )

        return new_access, new_refresh

    def revoke(self, refresh_token: str) -> None:
        token_hash = jwt_utils.token_fingerprint(refresh_token)
        stored = self._repository.get_refresh_token_by_hash(token_hash)
        if stored is not None:
            self._repository.revoke_refresh_token(stored.id)

    def parse_access_token(self, token: str) -> dict[str, object]:
        payload = jwt_utils.decode_token(token, self._config.security.jwt_secret)
        if payload.get("type") != "access":
            raise ValueError("Invalid access token")
        return payload
