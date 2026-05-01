import pytest
from models import UserRole, UserStatus

REGISTER_BASE = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone_number": "9876543210",
    "address": "123 Main Street City",
    "password": "TestPass1!",
    "role": "Customer",
}


def reg(**overrides):
    return {**REGISTER_BASE, **overrides}


# ── Registration ──────────────────────────────────────────────────────────────

class TestRegister:
    def test_customer_created_with_active_status(self, client):
        r = client.post("/api/auth/register", json=REGISTER_BASE)
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "Active"
        assert data["role"] == "Customer"
        assert data["email"] == "john@example.com"

    def test_vendor_created_with_pending_status(self, client):
        r = client.post("/api/auth/register", json=reg(
            email="vendor@test.com", role="Vendor", gst_number="29ABCDE1234F1Z5"
        ))
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "Pending"
        assert data["role"] == "Vendor"

    def test_password_not_returned_in_response(self, client):
        r = client.post("/api/auth/register", json=REGISTER_BASE)
        assert "password" not in r.json()
        assert "password_hash" not in r.json()

    def test_admin_self_register_blocked(self, client):
        r = client.post("/api/auth/register", json=reg(role="Admin"))
        assert r.status_code == 422

    def test_duplicate_email_returns_400(self, client):
        client.post("/api/auth/register", json=REGISTER_BASE)
        r = client.post("/api/auth/register", json=REGISTER_BASE)
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]

    def test_weak_password_no_uppercase(self, client):
        r = client.post("/api/auth/register", json=reg(password="nouppercas1!"))
        assert r.status_code == 422

    def test_weak_password_no_number(self, client):
        r = client.post("/api/auth/register", json=reg(password="NoNumbers!!"))
        assert r.status_code == 422

    def test_weak_password_no_special_char(self, client):
        r = client.post("/api/auth/register", json=reg(password="NoSpecial1A"))
        assert r.status_code == 422

    def test_weak_password_too_short(self, client):
        r = client.post("/api/auth/register", json=reg(password="Ab1!"))
        assert r.status_code == 422

    def test_invalid_phone_too_short(self, client):
        r = client.post("/api/auth/register", json=reg(phone_number="123"))
        assert r.status_code == 422

    def test_address_too_short(self, client):
        r = client.post("/api/auth/register", json=reg(address="Short"))
        assert r.status_code == 422

    def test_invalid_gst_format(self, client):
        r = client.post("/api/auth/register", json=reg(
            role="Vendor", gst_number="INVALID"
        ))
        assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_active_admin_login_returns_tokens(self, client, db, make_user):
        make_user(db, email="admin@test.com", role=UserRole.ADMIN, status=UserStatus.ACTIVE)
        r = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "TestPass1!"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "Admin"

    def test_active_customer_login_succeeds(self, client, db, make_user):
        make_user(db, email="cust@test.com", role=UserRole.CUSTOMER, status=UserStatus.ACTIVE)
        r = client.post("/api/auth/login", json={"email": "cust@test.com", "password": "TestPass1!"})
        assert r.status_code == 200

    def test_approved_vendor_login_succeeds(self, client, db, make_user):
        make_user(db, email="approved@test.com", role=UserRole.VENDOR, status=UserStatus.ACTIVE)
        r = client.post("/api/auth/login", json={"email": "approved@test.com", "password": "TestPass1!"})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "Vendor"

    def test_pending_vendor_login_blocked_with_403(self, client, db, make_user):
        make_user(db, email="pending@test.com", role=UserRole.VENDOR, status=UserStatus.PENDING)
        r = client.post("/api/auth/login", json={"email": "pending@test.com", "password": "TestPass1!"})
        assert r.status_code == 403
        assert "pending" in r.json()["detail"].lower()

    def test_inactive_user_login_blocked_with_403(self, client, db, make_user):
        make_user(db, email="inactive@test.com", status=UserStatus.INACTIVE)
        r = client.post("/api/auth/login", json={"email": "inactive@test.com", "password": "TestPass1!"})
        assert r.status_code == 403
        assert "deactivated" in r.json()["detail"].lower()

    def test_wrong_password_returns_401(self, client, db, make_user):
        make_user(db, email="user@test.com")
        r = client.post("/api/auth/login", json={"email": "user@test.com", "password": "WrongPass!"})
        assert r.status_code == 401

    def test_wrong_password_shows_remaining_attempts(self, client, db, make_user):
        make_user(db, email="user@test.com")
        r = client.post("/api/auth/login", json={"email": "user@test.com", "password": "WrongPass!"})
        assert "attempt" in r.json()["detail"].lower()

    def test_nonexistent_email_returns_401(self, client):
        r = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "TestPass1!"})
        assert r.status_code == 401

    def test_lockout_after_five_failed_attempts(self, client, db, make_user):
        make_user(db, email="lockout@test.com")
        for _ in range(5):
            client.post("/api/auth/login", json={"email": "lockout@test.com", "password": "WrongPass!"})
        r = client.post("/api/auth/login", json={"email": "lockout@test.com", "password": "TestPass1!"})
        assert r.status_code == 429
        assert "locked" in r.json()["detail"].lower()

    def test_correct_password_after_partial_failures_succeeds(self, client, db, make_user):
        make_user(db, email="partial@test.com")
        for _ in range(3):
            client.post("/api/auth/login", json={"email": "partial@test.com", "password": "WrongPass!"})
        r = client.post("/api/auth/login", json={"email": "partial@test.com", "password": "TestPass1!"})
        assert r.status_code == 200

    def test_status_not_returned_for_pending_vendor(self, client, db, make_user):
        make_user(db, email="pv@test.com", role=UserRole.VENDOR, status=UserStatus.PENDING)
        r = client.post("/api/auth/login", json={"email": "pv@test.com", "password": "TestPass1!"})
        assert "access_token" not in r.json()


# ── Token Refresh ─────────────────────────────────────────────────────────────

class TestRefreshToken:
    def _login(self, client, db, make_user, email="refresh@test.com"):
        make_user(db, email=email)
        r = client.post("/api/auth/login", json={"email": email, "password": "TestPass1!"})
        return r.json()["access_token"], r.json()["refresh_token"]

    def test_valid_refresh_token_returns_new_tokens(self, client, db, make_user):
        _, refresh = self._login(client, db, make_user)
        r = client.post("/api/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert "refresh_token" in r.json()

    def test_access_token_rejected_as_refresh(self, client, db, make_user):
        access, _ = self._login(client, db, make_user)
        r = client.post("/api/auth/refresh", json={"refresh_token": access})
        assert r.status_code == 401

    def test_invalid_token_string_returns_401(self, client):
        r = client.post("/api/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert r.status_code == 401
