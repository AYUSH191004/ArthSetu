# ============================================================
# FILE: backend/app/api/v1/routes/auth.py
# ============================================================

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.api.deps import AdminUser, CurrentUser
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.db.session import get_db
from backend.app.schemas import (
    ChangePasswordRequest,
    LoginResponse,
    PasswordResetRequest,
    UserCreate,
    UserOut,
    UserUpdate,
)
from backend.app.services import user_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
):
    user = user_service.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(subject=user.username, role=role)
    return LoginResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut(**user_service.to_out(user)),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser):
    return UserOut(**user_service.to_out(current_user))


@router.post("/change-password", status_code=204)
def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    try:
        user_service.change_own_password(
            db, current_user, body.current_password, body.new_password
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ------------------------------------------------------------
# Admin — user management
# ------------------------------------------------------------

@router.get("/users", response_model=list[UserOut])
def list_users(_: AdminUser, db: DbSession):
    return [UserOut(**user_service.to_out(u)) for u in user_service.list_users(db)]


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, _: AdminUser, db: DbSession):
    try:
        user = user_service.create_user(
            db,
            username=body.username,
            full_name=body.full_name,
            password=body.password,
            role=body.role,
            email=body.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return UserOut(**user_service.to_out(user))


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    body: UserUpdate,
    _: AdminUser,
    db: DbSession,
):
    try:
        user = user_service.update_user(db, user_id, **body.model_dump())
    except ValueError as exc:
        code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=code, detail=str(exc))
    return UserOut(**user_service.to_out(user))


@router.post("/users/{user_id}/reset-password", response_model=UserOut)
def reset_password(
    user_id: str,
    body: PasswordResetRequest,
    _: AdminUser,
    db: DbSession,
):
    try:
        user = user_service.set_password(db, user_id, body.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return UserOut(**user_service.to_out(user))
