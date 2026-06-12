"""
Authentication service — user registration, login, token management.
"""

from sqlalchemy.orm import Session
from database.models import User
from utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from utils.exceptions import DuplicateException, NotFoundException, UnauthorizedException


def register_user(db: Session, username: str, email: str, password: str,
                  full_name: str = "", phone: str = "", role: str = "patient") -> dict:
    """Register a new user. Returns user dict + tokens."""
    # Check duplicates
    if db.query(User).filter(User.username == username).first():
        raise DuplicateException("Username")
    if db.query(User).filter(User.email == email).first():
        raise DuplicateException("Email")

    # Validate role
    valid_roles = ["admin", "pharmacist", "patient"]
    if role not in valid_roles:
        role = "patient"

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        phone=phone,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate tokens (sub must be string for python-jose)
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


def login_user(db: Session, username: str, password: str) -> dict:
    """Authenticate user and return tokens."""
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Invalid username or password")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


def get_all_users(db: Session, role: str = None) -> list:
    """Get all users, optionally filtered by role."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return [u.to_dict() for u in query.order_by(User.created_at.desc()).all()]
