# =========================================================
# Auth Validator Tests
# =========================================================
#
# This file tests:
#
# auth_validators.py
#
# Covered areas:
#
# 1. Email normalization
#    - Lowercasing
#    - Trimming
#    - Invalid format rejection
#    - Excessive length rejection
#
# 2. Username normalization
#    - Lowercasing
#    - Trimming
#
# 3. Name trimming
#
# 4. Name validation
#    - Valid names
#    - Invalid characters
#    - Length boundaries
#
# 5. Username validation
#    - Valid usernames
#    - Invalid characters
#    - Length boundaries
#
# 6. Public role validation
#    - Allowed roles
#    - Forbidden roles
#
# =========================================================

import pytest

from app.core.enums import (
    UserRole,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.services.auth.auth_validators import (
    normalize_email,
    normalize_username,
    trim_name,
    validate_name,
    validate_username,
    validate_public_role,
)

# =========================================================
# normalize_email
# =========================================================


def test_normalize_email_success():

    result = normalize_email(
        "  TEST@Example.COM  ",
    )

    assert result == "test@example.com"


def test_normalize_email_invalid_format():

    with pytest.raises(AuthError) as exc:

        normalize_email(
            "not-an-email",
        )

    assert exc.value.code == "INVALID_EMAIL_FORMAT"


def test_normalize_email_exceeds_max_length():

    oversized_email = ("a" * 250) + "@x.com"

    with pytest.raises(AuthError) as exc:

        normalize_email(
            oversized_email,
        )

    assert exc.value.code == "INVALID_EMAIL_FORMAT"


# =========================================================
# normalize_username
# =========================================================


def test_normalize_username():

    result = normalize_username(
        "  Varun_User  ",
    )

    assert result == "varun_user"


# =========================================================
# trim_name
# =========================================================


def test_trim_name():

    result = trim_name(
        "   Varun Sharma   ",
    )

    assert result == "Varun Sharma"


# =========================================================
# validate_name
# =========================================================


def test_validate_name_success():

    assert validate_name(
        "Varun Sharma",
    )


def test_validate_name_with_apostrophe():

    assert validate_name(
        "O'Connor",
    )


def test_validate_name_with_hyphen():

    assert validate_name(
        "Anne-Marie",
    )


def test_validate_name_too_short():

    assert not validate_name(
        "A",
    )


def test_validate_name_too_long():

    assert not validate_name(
        "A" * 51,
    )


def test_validate_name_invalid_characters():

    assert not validate_name(
        "Varun123",
    )


# =========================================================
# validate_username
# =========================================================


def test_validate_username_success():

    assert validate_username(
        "varun_123",
    )


def test_validate_username_too_short():

    assert not validate_username(
        "ab",
    )


def test_validate_username_too_long():

    assert not validate_username(
        "a" * 31,
    )


def test_validate_username_invalid_characters():

    assert not validate_username(
        "varun@123",
    )


# =========================================================
# validate_public_role
# =========================================================


def test_validate_public_role_listener():

    assert validate_public_role(
        UserRole.LISTENER.value,
    )


def test_validate_public_role_artist():

    assert validate_public_role(
        UserRole.ARTIST.value,
    )


def test_validate_public_role_admin_rejected():

    assert not validate_public_role(
        UserRole.ADMIN.value,
    )


def test_validate_public_role_invalid_role():

    assert not validate_public_role(
        "superuser",
    )
