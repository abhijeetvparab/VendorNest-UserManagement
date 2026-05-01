from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_differs_from_plain(self):
        assert hash_password("TestPass1!") != "TestPass1!"

    def test_correct_password_verifies(self):
        hashed = hash_password("TestPass1!")
        assert verify_password("TestPass1!", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("TestPass1!")
        assert verify_password("WrongPass!", hashed) is False

    def test_empty_password_fails(self):
        hashed = hash_password("TestPass1!")
        assert verify_password("", hashed) is False

    def test_same_password_produces_different_hashes(self):
        # bcrypt salts every hash independently
        h1 = hash_password("TestPass1!")
        h2 = hash_password("TestPass1!")
        assert h1 != h2

    def test_both_hashes_still_verify(self):
        h1 = hash_password("TestPass1!")
        h2 = hash_password("TestPass1!")
        assert verify_password("TestPass1!", h1) is True
        assert verify_password("TestPass1!", h2) is True


class TestTokenCreation:
    def test_access_token_type_field(self):
        token = create_access_token({"sub": "uid-1", "role": "Admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "access"

    def test_access_token_carries_sub_and_role(self):
        token = create_access_token({"sub": "uid-1", "role": "Vendor"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "uid-1"
        assert payload["role"] == "Vendor"

    def test_refresh_token_type_field(self):
        token = create_refresh_token({"sub": "uid-1", "role": "Customer"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"

    def test_refresh_token_carries_sub(self):
        token = create_refresh_token({"sub": "uid-42"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "uid-42"

    def test_access_token_expires_in_future(self):
        token = create_access_token({"sub": "uid"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_custom_expiry_applied(self):
        delta = timedelta(minutes=5)
        token = create_access_token({"sub": "uid"}, expires_delta=delta)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expected = (datetime.now(timezone.utc) + delta).timestamp()
        assert abs(payload["exp"] - expected) < 5  # within 5 seconds


class TestTokenDecode:
    def test_decode_valid_access_token(self):
        token = create_access_token({"sub": "uid-1", "role": "Admin"})
        payload = decode_token(token)
        assert payload["sub"] == "uid-1"
        assert payload["role"] == "Admin"

    def test_decode_valid_refresh_token(self):
        token = create_refresh_token({"sub": "uid-2"})
        payload = decode_token(token)
        assert payload["sub"] == "uid-2"
        assert payload["type"] == "refresh"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("not.a.valid.token")
        assert exc.value.status_code == 401

    def test_tampered_token_raises_401(self):
        token = create_access_token({"sub": "uid"})
        tampered = token[:-4] + "xxxx"
        with pytest.raises(HTTPException) as exc:
            decode_token(tampered)
        assert exc.value.status_code == 401

    def test_empty_string_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("")
        assert exc.value.status_code == 401
