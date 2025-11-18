"""Authentication routes"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.utils.auth import verify_password, create_access_token, get_current_user
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""

    # Find user
    user = db.query(User).filter(User.username == request.username).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    return {"message": "Logged out successfully"}


@router.get("/status", response_model=UserResponse)
def get_auth_status(current_user: User = Depends(get_current_user)):
    """Get current authentication status"""
    return current_user


@router.post("/change-password")
def change_password(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    from app.utils.auth import verify_password, get_password_hash

    current_password = request.get("current_password")
    new_password = request.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required"
        )

    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    # Update password
    current_user.password_hash = get_password_hash(new_password)
    db.commit()

    return {
        "success": True,
        "message": "Password changed successfully"
    }
