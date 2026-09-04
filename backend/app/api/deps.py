# ============================================================
# FILE: backend/app/api/deps.py
# Authentication & authorization dependencies.
# ============================================================

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.security import decode_access_token
from backend.app.db.enums import UserRole
from backend.app.db.models.user import User
from backend.app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise _CREDENTIALS_EXC
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise _CREDENTIALS_EXC
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(minimum: UserRole):
    """Dependency: the current user's role must be >= `minimum`."""

    def _dep(user: CurrentUser) -> User:
        current = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if not current.satisfies(minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {minimum.value} role",
            )
        return user

    return _dep


require_reviewer = require_role(UserRole.REVIEWER)
require_admin = require_role(UserRole.ADMIN)

ReviewerUser = Annotated[User, Depends(require_reviewer)]
AdminUser = Annotated[User, Depends(require_admin)]
