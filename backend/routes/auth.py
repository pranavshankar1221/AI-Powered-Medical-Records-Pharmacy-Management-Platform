"""
Authentication routes — login, register, refresh token, profile.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.base import get_db
from schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse,
    RefreshTokenRequest, UpdateProfileRequest,
)
from services.auth_service import register_user, login_user
from utils.security import get_current_user, decode_token, create_access_token
from database.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    result = register_user(
        db=db,
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        phone=req.phone,
        role=req.role,
    )
    return {"success": True, **result}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    result = login_user(db=db, username=req.username, password=req.password)
    return {"success": True, **result}


@router.post("/refresh")
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh an expired access token."""
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    user_id_str = payload.get("sub")
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid refresh token subject")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "success": True,
        "access_token": new_access,
        "token_type": "bearer",
    }


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return {"success": True, "user": current_user.to_dict()}


@router.put("/me")
def update_profile(
    req: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile."""
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.email is not None:
        existing = db.query(User).filter(User.email == req.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        current_user.email = req.email
    db.commit()
    db.refresh(current_user)
    return {"success": True, "user": current_user.to_dict()}
