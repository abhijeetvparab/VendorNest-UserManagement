from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole, UserStatus, City
from schemas import (
    UserResponse, UserUpdate, UserStatusUpdate,
    CreateAdminRequest, CityResponse,
)
from auth import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/cities", response_model=List[CityResponse])
def list_cities(db: Session = Depends(get_db)):
    return db.query(City).order_by(City.city).all()


@router.get("", response_model=List[UserResponse])
def list_users(
    role:   Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip:   int = 0,
    limit:  int = 50,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if role:   q = q.filter(User.role   == role)
    if status: q = q.filter(User.status == status)
    if search:
        s = f"%{search}%"
        q = q.filter(
            User.first_name.ilike(s) | User.last_name.ilike(s) | User.email.ilike(s)
        )
    return q.offset(skip).limit(limit).all()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


@router.patch("/{user_id}/status", response_model=UserResponse)
def toggle_status(
    user_id: str,
    data: UserStatusUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = data.status
    db.commit()
    db.refresh(user)
    return user


@router.post("/admin", response_model=UserResponse, status_code=201)
def create_admin(
    data: CreateAdminRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        first_name    = data.first_name,
        last_name     = data.last_name,
        email         = data.email,
        phone_number  = data.phone_number,
        address       = data.address,
        password_hash = hash_password(data.password),
        role          = UserRole.ADMIN,
        status        = UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
