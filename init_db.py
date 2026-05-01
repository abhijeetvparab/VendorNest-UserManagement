"""
Run once to create MySQL tables and seed demo data.
    python init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import uuid
from datetime import datetime
from common.database import engine, SessionLocal
from common.models import Base, User, VendorProfile, UserRole, UserStatus, OnboardingStatus
from common.auth_utils import hash_password


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables created")


def seed():
    db = SessionLocal()
    if db.query(User).count() > 0:
        print("[INFO] Database already seeded -- skipping.")
        db.close()
        return

    admin = User(
        id            = str(uuid.uuid4()),
        first_name    = "Alice",
        last_name     = "Admin",
        email         = "admin@vendornest.com",
        phone_number  = "9000000001",
        address       = "1 Admin Lane, HQ City",
        password_hash = hash_password("admin123"),
        role          = UserRole.ADMIN,
        status        = UserStatus.ACTIVE,
    )

    vendor_user = User(
        id            = str(uuid.uuid4()),
        first_name    = "Victor",
        last_name     = "Vendor",
        email         = "vendor@vendornest.com",
        phone_number  = "9000000002",
        address       = "22 Vendor Street, Biz City",
        gst_number    = "29ABCDE1234F1Z5",
        password_hash = hash_password("vendor123"),
        role          = UserRole.VENDOR,
        status        = UserStatus.PENDING,
    )

    customer = User(
        id            = str(uuid.uuid4()),
        first_name    = "Charlie",
        last_name     = "Customer",
        email         = "customer@vendornest.com",
        phone_number  = "9000000003",
        address       = "55 Green Park, Home City",
        password_hash = hash_password("cust123"),
        role          = UserRole.CUSTOMER,
        status        = UserStatus.ACTIVE,
    )

    db.add_all([admin, vendor_user, customer])
    db.commit()

    vendor_profile = VendorProfile(
        id                = str(uuid.uuid4()),
        user_id           = vendor_user.id,
        business_name     = "Victor's Electronics Hub",
        business_type     = "Electronics",
        business_address  = "22 Vendor Street, Biz City",
        gst_number        = "29ABCDE1234F1Z5",
        poc_name          = "Victor Vendor",
        poc_phone         = "9000000002",
        poc_email         = "victor@ehub.com",
        description       = "Premium electronics and gadgets sourced directly from manufacturers.",
        document_name     = "biz_license_2024.pdf",
        onboarding_status = OnboardingStatus.PENDING,
        submitted_at      = datetime.utcnow(),
    )
    db.add(vendor_profile)
    db.commit()
    db.close()

    print("[OK] Seeded successfully!")
    print("   admin@vendornest.com    / admin123")
    print("   vendor@vendornest.com   / vendor123")
    print("   customer@vendornest.com / cust123")


if __name__ == "__main__":
    create_tables()
    seed()
