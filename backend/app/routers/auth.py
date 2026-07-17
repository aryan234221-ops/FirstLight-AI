from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.application import ApplicationContext
from app.db.database import get_db_session
from app.schemas.enterprise import LoginRequest, LoginResponse, RefreshRequest


router = APIRouter(prefix="/api/v2/auth", tags=["Auth"])
context = ApplicationContext()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)) -> LoginResponse:
    auth_service = context.auth_service_for_session(db)
    try:
        access_token, refresh_token, user = auth_service.authenticate(payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return LoginResponse(access_token=access_token, refresh_token=refresh_token, user=user)


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db_session)) -> dict[str, str]:
    auth_service = context.auth_service_for_session(db)
    try:
        access_token, refresh_token = auth_service.refresh(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db_session)) -> None:
    auth_service = context.auth_service_for_session(db)
    auth_service.revoke(payload.refresh_token)


@router.get("/me")
def me(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    return current_user
