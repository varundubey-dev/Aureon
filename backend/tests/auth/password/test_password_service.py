# =========================================================
# Password Service Tests
# =========================================================
#
# This file tests:
#
# password_service.py
#
# Covered areas:
#
# 1. Password hashing
#    - Hash generation
#    - Hash uniqueness
#    - Raw password mismatch
#
# 2. Password verification
#    - Correct password verification
#    - Incorrect password rejection
#
# 3. Password strength validation
#    - Minimum length enforcement
#    - Common weak password rejection
#    - Valid password acceptance
#
# 4. Unusable password generation
#    - Hash generation
#    - Randomness
#    - Non-empty output
#
# =========================================================

from app.services.auth.password_service import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_unusable_password_hash,
)

# =========================================================
# Password Hashing
# =========================================================


def test_hash_password_generates_hash():

    password = "StrongPassword123!"

    hashed = hash_password(
        password,
    )

    assert hashed != password

    assert isinstance(
        hashed,
        str,
    )

    assert len(hashed) > 0


def test_hash_password_generates_unique_hashes():

    password = "StrongPassword123!"

    hash_1 = hash_password(
        password,
    )

    hash_2 = hash_password(
        password,
    )

    # bcrypt salt should make hashes unique
    assert hash_1 != hash_2


# =========================================================
# Password Verification
# =========================================================


def test_verify_password_success():

    password = "StrongPassword123!"

    hashed = hash_password(
        password,
    )

    assert verify_password(
        password,
        hashed,
    )


def test_verify_password_failure():

    hashed = hash_password(
        "CorrectPassword123!",
    )

    assert not verify_password(
        "WrongPassword123!",
        hashed,
    )


# =========================================================
# Password Strength Validation
# =========================================================


def test_validate_password_strength_success():

    assert validate_password_strength(
        "StrongPassword123!",
    )


def test_validate_password_strength_too_short():

    assert not validate_password_strength(
        "short",
    )


def test_validate_password_strength_common_weak_password():

    assert not validate_password_strength(
        "password123",
    )


def test_validate_password_strength_case_insensitive_weak_password():

    assert not validate_password_strength(
        "PASSWORD123",
    )


# =========================================================
# Unusable Password Hash
# =========================================================


def test_generate_unusable_password_hash():

    unusable_hash = generate_unusable_password_hash()

    assert isinstance(
        unusable_hash,
        str,
    )

    assert len(unusable_hash) > 0


def test_generate_unusable_password_hash_is_random():

    hash_1 = generate_unusable_password_hash()

    hash_2 = generate_unusable_password_hash()

    assert hash_1 != hash_2
