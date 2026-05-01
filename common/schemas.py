import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from common.models import UserRole, UserStatus, OnboardingStatus


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    first_name:    str
    last_name:     str
    email:         EmailStr
    phone_number:  str
    address:       str
    gst_number:    Optional[str] = None
    document_name: Optional[str] = None
    password:      str
    role:          UserRole

    @field_validator("first_name", "last_name")
    @classmethod
    def alpha_only(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z ]{1,50}$", v.strip()):
            raise ValueError("Alpha characters only, max 50 chars")
        return v.strip()

    @field_validator("phone_number")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        if not re.match(r"^\+?[0-9]{10,15}$", v.strip()):
            raise ValueError("10-15 digit phone number (optional country code)")
        return v.strip()

    @field_validator("address")
    @classmethod
    def min_address(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Address must be at least 10 characters")
        return v.strip()

    @field_validator("gst_number")
    @classmethod
    def valid_gst(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[0-9A-Z]{15}$", v.upper()):
            raise ValueError("GST must be 15-char alphanumeric")
        return v.upper() if v else None

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        errors = []
        if len(v) < 8:                  errors.append("min 8 characters")
        if not re.search(r"[A-Z]", v):  errors.append("1 uppercase letter")
        if not re.search(r"[0-9]", v):  errors.append("1 number")
        if not re.search(r"[^A-Za-z0-9]", v): errors.append("1 special character")
        if errors:
            raise ValueError("Password needs: " + ", ".join(errors))
        return v

    @field_validator("role")
    @classmethod
    def no_admin_self_register(cls, v: UserRole) -> UserRole:
        if v == UserRole.ADMIN:
            raise ValueError("Admins cannot self-register")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ──────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id:           str
    first_name:   str
    last_name:    str
    email:        str
    phone_number: str
    address:      str
    gst_number:   Optional[str]
    role:         UserRole
    status:       UserStatus
    created_at:   datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name:   Optional[str] = None
    last_name:    Optional[str] = None
    phone_number: Optional[str] = None
    address:      Optional[str] = None


class UserStatusUpdate(BaseModel):
    status: UserStatus


class CreateAdminRequest(BaseModel):
    first_name:   str
    last_name:    str
    email:        EmailStr
    password:     str
    phone_number: str
    address:      str


# ── Vendor ────────────────────────────────────────────────────────────────────

class VendorOnboardingRequest(BaseModel):
    business_name:    str
    business_type:    str
    business_address: str
    gst_number:       Optional[str] = None
    poc_name:         str
    poc_phone:        str
    poc_email:        EmailStr
    description:      Optional[str] = None
    document_name:    Optional[str] = None

    @field_validator("description")
    @classmethod
    def max_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError("Description must be 500 characters or fewer")
        return v

    @field_validator("gst_number")
    @classmethod
    def valid_gst(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[0-9A-Z]{15}$", v.upper()):
            raise ValueError("GST must be 15-char alphanumeric")
        return v.upper() if v else None


class VendorRejectRequest(BaseModel):
    reason: str


class VendorProfileResponse(BaseModel):
    id:                str
    user_id:           str
    business_name:     str
    business_type:     str
    business_address:  str
    gst_number:        Optional[str]
    poc_name:          str
    poc_phone:         str
    poc_email:         str
    description:       Optional[str]
    document_name:     Optional[str]
    onboarding_status: OnboardingStatus
    rejection_reason:  Optional[str]
    reviewed_by:       Optional[str]
    reviewed_at:       Optional[datetime]
    submitted_at:      datetime
    user:              Optional[UserResponse] = None

    model_config = {"from_attributes": True}


# ── City ──────────────────────────────────────────────────────────────────────

class CityResponse(BaseModel):
    id:    int
    city:  str
    state: str

    model_config = {"from_attributes": True}


TokenResponse.model_rebuild()
