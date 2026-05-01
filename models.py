import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Enum, ForeignKey, Index
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    VENDOR = "Vendor"
    CUSTOMER = "Customer"


class UserStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"


class OnboardingStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class User(Base):
    __tablename__ = "users"

    id             = Column(CHAR(36), primary_key=True, default=gen_uuid)
    first_name     = Column(String(50), nullable=False)
    last_name      = Column(String(50), nullable=False)
    email          = Column(String(150), unique=True, nullable=False, index=True)
    phone_number   = Column(String(20), nullable=False)
    address        = Column(Text, nullable=False)
    gst_number     = Column(String(15), nullable=True)
    password_hash  = Column(String(255), nullable=False)
    role           = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    status         = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING)
    failed_attempts= Column(Integer, default=0)
    locked_until   = Column(DateTime, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor_profile = relationship(
        "VendorProfile", back_populates="user",
        foreign_keys="VendorProfile.user_id", uselist=False
    )


class VendorProfile(Base):
    __tablename__ = "vendor_profiles"

    id                = Column(CHAR(36), primary_key=True, default=gen_uuid)
    user_id           = Column(CHAR(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    business_name     = Column(String(150), nullable=False)
    business_type     = Column(String(100), nullable=False)
    business_address  = Column(Text, nullable=False)
    pincode           = Column(String(10), nullable=True)
    gst_number        = Column(String(15), nullable=True)
    poc_name          = Column(String(100), nullable=False)
    poc_phone         = Column(String(20), nullable=False)
    poc_email         = Column(String(150), nullable=False)
    description       = Column(Text, nullable=True)
    document_name     = Column(String(255), nullable=True)
    onboarding_status = Column(Enum(OnboardingStatus), nullable=False, default=OnboardingStatus.PENDING)
    rejection_reason  = Column(Text, nullable=True)
    reviewed_by       = Column(CHAR(36), ForeignKey("users.id"), nullable=True)
    reviewed_at       = Column(DateTime, nullable=True)
    submitted_at      = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="vendor_profile", foreign_keys=[user_id])


class City(Base):
    __tablename__ = "city"

    id    = Column(Integer, primary_key=True, autoincrement=True)
    city  = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
