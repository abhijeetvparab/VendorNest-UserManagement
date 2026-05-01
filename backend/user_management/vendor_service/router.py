from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from common.database import get_db
from common.models import User, VendorProfile, OnboardingStatus, UserRole, UserStatus
from common.schemas import (
    VendorOnboardingRequest, VendorProfileResponse, VendorRejectRequest,
)
from common.auth_utils import get_current_user, require_admin

router = APIRouter(prefix="/api/vendors", tags=["Vendors"])


@router.post("/onboarding", response_model=VendorProfileResponse, status_code=201)
def submit_onboarding(
    data: VendorOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can submit onboarding")

    existing = db.query(VendorProfile).filter(VendorProfile.user_id == current_user.id).first()
    if existing:
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(existing, k, v)
        existing.onboarding_status = OnboardingStatus.PENDING
        existing.rejection_reason  = None
        existing.reviewed_by       = None
        existing.reviewed_at       = None
        existing.submitted_at      = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    profile = VendorProfile(user_id=current_user.id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/onboarding", response_model=List[VendorProfileResponse])
def list_onboarding(
    status: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(VendorProfile).options(joinedload(VendorProfile.user))
    if status:
        q = q.filter(VendorProfile.onboarding_status == status)
    return q.order_by(VendorProfile.submitted_at.desc()).all()


@router.get("/onboarding/mine", response_model=VendorProfileResponse)
def get_my_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(VendorProfile).filter(VendorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No onboarding submission found")
    return profile


@router.get("/onboarding/{profile_id}", response_model=VendorProfileResponse)
def get_onboarding(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(VendorProfile)
        .options(joinedload(VendorProfile.user))
        .filter(VendorProfile.id == profile_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role != UserRole.ADMIN and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return profile


@router.patch("/onboarding/{profile_id}/approve", response_model=VendorProfileResponse)
def approve_vendor(
    profile_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    profile = db.query(VendorProfile).filter(VendorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Not found")
    profile.onboarding_status = OnboardingStatus.APPROVED
    profile.reviewed_by       = current_user.id
    profile.reviewed_at       = datetime.utcnow()
    vendor_user = db.query(User).filter(User.id == profile.user_id).first()
    if vendor_user:
        vendor_user.status = UserStatus.ACTIVE
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/onboarding/{profile_id}/reject", response_model=VendorProfileResponse)
def reject_vendor(
    profile_id: str,
    data: VendorRejectRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not data.reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")
    profile = db.query(VendorProfile).filter(VendorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Not found")
    profile.onboarding_status = OnboardingStatus.REJECTED
    profile.rejection_reason  = data.reason.strip()
    profile.reviewed_by       = current_user.id
    profile.reviewed_at       = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/approved", response_model=List[VendorProfileResponse])
def list_approved_vendors(
    search:        Optional[str] = None,
    business_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(VendorProfile)
        .options(joinedload(VendorProfile.user))
        .filter(VendorProfile.onboarding_status == OnboardingStatus.APPROVED)
    )
    if business_type:
        q = q.filter(VendorProfile.business_type == business_type)
    if search:
        s = f"%{search}%"
        q = q.filter(
            VendorProfile.business_name.ilike(s) | VendorProfile.business_type.ilike(s)
        )
    return q.all()
