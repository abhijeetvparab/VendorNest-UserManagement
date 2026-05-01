from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole, UserStatus
from schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserResponse,
)
from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

MAX_FAILED       = 5
LOCKOUT_MINUTES  = 15


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        first_name    = data.first_name,
        last_name     = data.last_name,
        email         = data.email,
        phone_number  = data.phone_number,
        address       = data.address,
        gst_number    = data.gst_number,
        password_hash = hash_password(data.password),
        role          = data.role,
        status        = (UserStatus.PENDING if data.role == UserRole.VENDOR
                         else UserStatus.ACTIVE),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials. Please check email and password.")

    # Lockout check
    if user.locked_until and datetime.utcnow() < user.locked_until:
        remaining = max(1, int((user.locked_until - datetime.utcnow()).total_seconds() / 60))
        raise HTTPException(
            status_code=429,
            detail=f"Account locked. Try again in {remaining} minute(s).",
        )

    if not verify_password(data.password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= MAX_FAILED:
            user.locked_until   = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_attempts = 0
            db.commit()
            raise HTTPException(
                status_code=429,
                detail="Account locked for 15 minutes after 5 failed attempts.",
            )
        db.commit()
        left = MAX_FAILED - user.failed_attempts
        raise HTTPException(
            status_code=401,
            detail=f"Invalid credentials. {left} attempt(s) remaining.",
        )

    # Status check — block pending/inactive accounts before issuing tokens
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=403,
            detail="Your account is pending admin approval. You will be notified once approved.",
        )
    if user.status == UserStatus.INACTIVE:
        raise HTTPException(
            status_code=403,
            detail="Your account has been deactivated. Please contact support.",
        )

    # Success
    user.failed_attempts = 0
    user.locked_until    = None
    db.commit()

    token_data = {"sub": user.id, "role": user.role.value}
    return TokenResponse(
        access_token  = create_access_token(token_data),
        refresh_token = create_refresh_token(token_data),
        user          = UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    token_data = {"sub": user.id, "role": user.role.value}
    return TokenResponse(
        access_token  = create_access_token(token_data),
        refresh_token = create_refresh_token(token_data),
        user          = UserResponse.model_validate(user),
    )


@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    # In production: send reset email via SendGrid / Nodemailer equivalent
    db.query(User).filter(User.email == email).first()  # existence check (don't leak)
    return {"message": "If that email exists, a reset link has been sent."}
