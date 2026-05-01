import pytest
from pydantic import ValidationError

from models import UserRole
from schemas import RegisterRequest

BASE = dict(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    phone_number="9876543210",
    address="123 Main Street City",
    password="TestPass1!",
    role=UserRole.CUSTOMER,
)


def valid(**overrides):
    return {**BASE, **overrides}


# ── Password ──────────────────────────────────────────────────────────────────

class TestPasswordValidation:
    def test_strong_password_accepted(self):
        req = RegisterRequest(**BASE)
        assert req.password == "TestPass1!"

    def test_no_uppercase_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(password="nouppercas1!"))

    def test_no_number_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(password="NoNumbers!!"))

    def test_no_special_char_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(password="NoSpecial1A"))

    def test_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(password="Ab1!"))

    def test_exactly_8_chars_accepted(self):
        req = RegisterRequest(**valid(password="TestP1!x"))
        assert req.password == "TestP1!x"


# ── GST Number ────────────────────────────────────────────────────────────────

class TestGstValidation:
    def test_valid_gst_accepted(self):
        req = RegisterRequest(**valid(gst_number="29ABCDE1234F1Z5"))
        assert req.gst_number == "29ABCDE1234F1Z5"

    def test_gst_normalised_to_uppercase(self):
        req = RegisterRequest(**valid(gst_number="29abcde1234f1z5"))
        assert req.gst_number == "29ABCDE1234F1Z5"

    def test_invalid_gst_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(gst_number="TOOSHORT"))

    def test_invalid_gst_too_long_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(gst_number="29ABCDE1234F1Z567"))

    def test_none_gst_accepted(self):
        req = RegisterRequest(**valid(gst_number=None))
        assert req.gst_number is None


# ── Role ──────────────────────────────────────────────────────────────────────

class TestRoleValidation:
    def test_customer_role_accepted(self):
        req = RegisterRequest(**BASE)
        assert req.role == UserRole.CUSTOMER

    def test_vendor_role_accepted(self):
        req = RegisterRequest(**valid(role=UserRole.VENDOR))
        assert req.role == UserRole.VENDOR

    def test_admin_role_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(role=UserRole.ADMIN))


# ── Field validators ──────────────────────────────────────────────────────────

class TestFieldValidation:
    def test_phone_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(phone_number="123"))

    def test_phone_with_country_code_accepted(self):
        req = RegisterRequest(**valid(phone_number="+919876543210"))
        assert req.phone_number == "+919876543210"

    def test_address_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(address="Short"))

    def test_address_exactly_10_chars_accepted(self):
        req = RegisterRequest(**valid(address="1234567890"))
        assert req.address == "1234567890"

    def test_name_with_digits_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(**valid(first_name="John123"))

    def test_name_with_spaces_accepted(self):
        req = RegisterRequest(**valid(first_name="Mary Jane"))
        assert req.first_name == "Mary Jane"

    def test_name_stripped_of_leading_trailing_spaces(self):
        req = RegisterRequest(**valid(first_name="  Alice  "))
        assert req.first_name == "Alice"
