import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from conftest import auth_header
from models import UserRole, UserStatus

# ── List Users ────────────────────────────────────────────────────────────────

class TestListUsers:
    def test_admin_receives_all_users(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        make_user(db, email="vendor@test.com", role=UserRole.VENDOR, status=UserStatus.PENDING)
        make_user(db, email="cust@test.com", role=UserRole.CUSTOMER)
        r = client.get("/api/users", headers=auth_header(admin))
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_non_admin_is_forbidden(self, client, db, make_user):
        user = make_user(db, email="user@test.com")
        r = client.get("/api/users", headers=auth_header(user))
        assert r.status_code == 403

    def test_unauthenticated_is_rejected(self, client):
        r = client.get("/api/users")
        assert r.status_code in (401, 403)

    def test_filter_by_role_returns_only_matching(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        make_user(db, email="vendor@test.com", role=UserRole.VENDOR, status=UserStatus.PENDING)
        make_user(db, email="cust@test.com", role=UserRole.CUSTOMER)
        r = client.get("/api/users?role=Vendor", headers=auth_header(admin))
        data = r.json()
        assert len(data) == 1
        assert data[0]["role"] == "Vendor"

    def test_filter_by_status_returns_only_matching(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        make_user(db, email="pending@test.com", status=UserStatus.PENDING)
        make_user(db, email="inactive@test.com", status=UserStatus.INACTIVE)
        r = client.get("/api/users?status=Pending", headers=auth_header(admin))
        data = r.json()
        assert all(u["status"] == "Pending" for u in data)

    def test_search_matches_first_name(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        make_user(db, email="alice@test.com", first_name="Alice", last_name="Brown")
        make_user(db, email="bob@test.com",   first_name="Bob",   last_name="Smith")
        r = client.get("/api/users?search=Alice", headers=auth_header(admin))
        data = r.json()
        assert len(data) == 1
        assert data[0]["email"] == "alice@test.com"

    def test_search_matches_email(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        make_user(db, email="findme@test.com")
        make_user(db, email="other@test.com")
        r = client.get("/api/users?search=findme", headers=auth_header(admin))
        assert len(r.json()) == 1

    def test_pagination_skip_and_limit(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        for i in range(5):
            make_user(db, email=f"user{i}@test.com")
        r = client.get("/api/users?skip=0&limit=3", headers=auth_header(admin))
        assert len(r.json()) == 3


# ── Get Me ────────────────────────────────────────────────────────────────────

class TestGetMe:
    def test_returns_own_profile(self, client, db, make_user):
        user = make_user(db, email="me@test.com")
        r = client.get("/api/users/me", headers=auth_header(user))
        assert r.status_code == 200
        assert r.json()["email"] == "me@test.com"

    def test_response_excludes_password(self, client, db, make_user):
        user = make_user(db, email="me@test.com")
        data = client.get("/api/users/me", headers=auth_header(user)).json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_unauthenticated_is_rejected(self, client):
        r = client.get("/api/users/me")
        assert r.status_code in (401, 403)


# ── Get User by ID ────────────────────────────────────────────────────────────

class TestGetUser:
    def test_admin_can_get_any_user(self, client, db, make_user):
        admin  = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        target = make_user(db, email="target@test.com")
        r = client.get(f"/api/users/{target.id}", headers=auth_header(admin))
        assert r.status_code == 200
        assert r.json()["email"] == "target@test.com"

    def test_user_can_get_own_profile(self, client, db, make_user):
        user = make_user(db, email="self@test.com")
        r = client.get(f"/api/users/{user.id}", headers=auth_header(user))
        assert r.status_code == 200

    def test_user_cannot_get_other_profile(self, client, db, make_user):
        user  = make_user(db, email="user@test.com")
        other = make_user(db, email="other@test.com")
        r = client.get(f"/api/users/{other.id}", headers=auth_header(user))
        assert r.status_code == 403

    def test_nonexistent_id_returns_404(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.get("/api/users/no-such-id", headers=auth_header(admin))
        assert r.status_code == 404


# ── Update User ───────────────────────────────────────────────────────────────

class TestUpdateUser:
    def test_user_can_update_own_first_name(self, client, db, make_user):
        user = make_user(db, email="user@test.com")
        r = client.put(f"/api/users/{user.id}",
                       json={"first_name": "Updated"},
                       headers=auth_header(user))
        assert r.status_code == 200
        assert r.json()["first_name"] == "Updated"

    def test_admin_can_update_any_user(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        user  = make_user(db, email="user@test.com")
        r = client.put(f"/api/users/{user.id}",
                       json={"first_name": "AdminSet"},
                       headers=auth_header(admin))
        assert r.status_code == 200
        assert r.json()["first_name"] == "AdminSet"

    def test_user_cannot_update_other_profile(self, client, db, make_user):
        user  = make_user(db, email="user@test.com")
        other = make_user(db, email="other@test.com")
        r = client.put(f"/api/users/{other.id}",
                       json={"first_name": "Hacked"},
                       headers=auth_header(user))
        assert r.status_code == 403

    def test_omitted_fields_are_unchanged(self, client, db, make_user):
        user = make_user(db, email="user@test.com",
                         first_name="Original", last_name="Name")
        r = client.put(f"/api/users/{user.id}",
                       json={"last_name": "Changed"},
                       headers=auth_header(user))
        data = r.json()
        assert data["first_name"] == "Original"
        assert data["last_name"]  == "Changed"

    def test_nonexistent_user_returns_404(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.put("/api/users/no-such-id",
                       json={"first_name": "X"},
                       headers=auth_header(admin))
        assert r.status_code == 404


# ── Delete User ───────────────────────────────────────────────────────────────

class TestDeleteUser:
    def test_admin_can_delete_another_user(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        user  = make_user(db, email="user@test.com")
        r = client.delete(f"/api/users/{user.id}", headers=auth_header(admin))
        assert r.status_code == 204

    def test_admin_cannot_delete_own_account(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.delete(f"/api/users/{admin.id}", headers=auth_header(admin))
        assert r.status_code == 400
        assert "own account" in r.json()["detail"].lower()

    def test_non_admin_cannot_delete_user(self, client, db, make_user):
        user  = make_user(db, email="user@test.com")
        other = make_user(db, email="other@test.com")
        r = client.delete(f"/api/users/{other.id}", headers=auth_header(user))
        assert r.status_code == 403

    def test_deleted_user_returns_404_on_fetch(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        user  = make_user(db, email="gone@test.com")
        client.delete(f"/api/users/{user.id}", headers=auth_header(admin))
        r = client.get(f"/api/users/{user.id}", headers=auth_header(admin))
        assert r.status_code == 404

    def test_nonexistent_user_returns_404(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.delete("/api/users/no-such-id", headers=auth_header(admin))
        assert r.status_code == 404


# ── Toggle Status ─────────────────────────────────────────────────────────────

class TestToggleStatus:
    def test_admin_can_deactivate_user(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        user  = make_user(db, email="user@test.com", status=UserStatus.ACTIVE)
        r = client.patch(f"/api/users/{user.id}/status",
                         json={"status": "Inactive"},
                         headers=auth_header(admin))
        assert r.status_code == 200
        assert r.json()["status"] == "Inactive"

    def test_admin_can_reactivate_user(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        user  = make_user(db, email="user@test.com", status=UserStatus.INACTIVE)
        r = client.patch(f"/api/users/{user.id}/status",
                         json={"status": "Active"},
                         headers=auth_header(admin))
        assert r.status_code == 200
        assert r.json()["status"] == "Active"

    def test_admin_can_approve_pending_vendor(self, client, db, make_user):
        admin  = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        vendor = make_user(db, email="v@test.com",
                           role=UserRole.VENDOR, status=UserStatus.PENDING)
        r = client.patch(f"/api/users/{vendor.id}/status",
                         json={"status": "Active"},
                         headers=auth_header(admin))
        assert r.json()["status"] == "Active"

    def test_non_admin_cannot_toggle_status(self, client, db, make_user):
        user  = make_user(db, email="user@test.com")
        other = make_user(db, email="other@test.com")
        r = client.patch(f"/api/users/{other.id}/status",
                         json={"status": "Inactive"},
                         headers=auth_header(user))
        assert r.status_code == 403

    def test_nonexistent_user_returns_404(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.patch("/api/users/no-such-id/status",
                         json={"status": "Active"},
                         headers=auth_header(admin))
        assert r.status_code == 404


# ── Create Admin ──────────────────────────────────────────────────────────────

class TestCreateAdmin:
    PAYLOAD = {
        "first_name":   "New",
        "last_name":    "Admin",
        "email":        "newadmin@test.com",
        "phone_number": "9876543210",
        "address":      "123 Admin Street City",
        "password":     "TestPass1!",
    }

    def test_admin_creates_new_admin_with_active_status(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.post("/api/users/admin",
                        json=self.PAYLOAD, headers=auth_header(admin))
        assert r.status_code == 201
        data = r.json()
        assert data["role"]   == "Admin"
        assert data["status"] == "Active"

    def test_new_admin_email_is_stored(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        r = client.post("/api/users/admin",
                        json=self.PAYLOAD, headers=auth_header(admin))
        assert r.json()["email"] == "newadmin@test.com"

    def test_duplicate_email_returns_400(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        client.post("/api/users/admin", json=self.PAYLOAD, headers=auth_header(admin))
        r = client.post("/api/users/admin", json=self.PAYLOAD, headers=auth_header(admin))
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]

    def test_non_admin_cannot_create_admin(self, client, db, make_user):
        user = make_user(db, email="user@test.com")
        r = client.post("/api/users/admin",
                        json=self.PAYLOAD, headers=auth_header(user))
        assert r.status_code == 403

    def test_password_not_in_response(self, client, db, make_user):
        admin = make_user(db, email="admin@test.com", role=UserRole.ADMIN)
        data = client.post("/api/users/admin",
                           json=self.PAYLOAD, headers=auth_header(admin)).json()
        assert "password"      not in data
        assert "password_hash" not in data
