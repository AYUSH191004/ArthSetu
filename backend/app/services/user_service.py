# ============================================================
# FILE: backend/app/services/user_service.py
# ============================================================

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, verify_password
from backend.app.db.enums import UserRole
from backend.app.db.models.user import User


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = get_by_username(db, username)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.username.asc()).all()


def create_user(
    db: Session,
    *,
    username: str,
    full_name: str,
    password: str,
    role: str = "viewer",
    email: str | None = None,
) -> User:
    if get_by_username(db, username):
        raise ValueError("Username already exists")
    user = User(
        username=username,
        full_name=full_name,
        email=email,
        role=UserRole(role),
        hashed_password=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get(db: Session, user_id: str) -> User:
    try:
        uid = UUID(str(user_id))
    except (ValueError, TypeError):
        raise ValueError("Invalid user id")
    user = db.get(User, uid)
    if not user:
        raise ValueError("User not found")
    return user


BOOTSTRAP_USERNAME = "admin"


def update_user(db: Session, user_id: str, **changes) -> User:
    user = _get(db, user_id)

    # The bootstrap admin must always remain an active admin.
    if user.username == BOOTSTRAP_USERNAME:
        if changes.get("is_active") is False:
            raise ValueError("The bootstrap admin cannot be disabled")
        if changes.get("role") not in (None, "admin"):
            raise ValueError("The bootstrap admin cannot be demoted")

    if changes.get("role") is not None:
        user.role = UserRole(changes["role"])
    for field in ("full_name", "email", "is_active"):
        if changes.get(field) is not None:
            setattr(user, field, changes[field])
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user_id: str, new_password: str) -> User:
    user = _get(db, user_id)
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def change_own_password(
    db: Session, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise ValueError("Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    db.commit()


def to_out(user: User) -> dict:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return {
        "id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }
