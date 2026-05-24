# =========================================================
# OTP Cleanup Tests
# =========================================================
#
# This file tests:
#
# cleanup_expired_otps()
#
# Covered areas:
#
# 1. Expired OTP cleanup
#    - Expired OTP deletion
#
# 2. Active OTP protection
#    - Non-expired OTP preservation
#
# 3. Signup cleanup behavior
#    - Pending signup deletion
#
# 4. Password reset isolation
#    - No pending signup deletion
#
# 5. Cleanup count tracking
#    - Correct deletion count returned
#
# NOTE:
#
# - Scheduler behavior is NOT tested here.
# - This file tests ONLY cleanup logic.
#
# =========================================================

from datetime import timedelta

from sqlmodel import (
    select,
)

from app.core.enums import (
    OTPPurpose,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.pending_signup import (
    PendingSignup,
)

from app.services.auth.otp_service import (
    hash_otp,
)

from app.services.maintenance.otp_cleanup import (
    cleanup_expired_otps,
)

from app.utils.datetime import (
    get_utc_now,
)

# =========================================================
# Helpers
# =========================================================


def create_otp(
    session,
    *,
    email,
    purpose,
    expired=True,
):

    expires_at = (
        get_utc_now() - timedelta(minutes=5)
        if expired
        else get_utc_now() + timedelta(minutes=5)
    )

    otp = OTP(
        email=email,
        purpose=purpose,
        otp_hash=hash_otp(
            "123456",
        ),
        expires_at=expires_at,
    )

    session.add(otp)
    session.commit()

    return otp


def create_pending_signup(
    session,
    *,
    email,
):

    pending_signup = PendingSignup(
        name="Varun",
        email=email,
        otp_hash=hash_otp(
            "123456",
        ),
        otp_expires_at=get_utc_now() + timedelta(minutes=5),
        verified=False,
    )

    session.add(
        pending_signup,
    )

    session.commit()

    return pending_signup


# =========================================================
# OTP Cleanup
# =========================================================


def test_cleanup_deletes_expired_signup_otp_and_pending_signup(
    session,
):

    email = "signupcleanup@example.com"

    create_otp(
        session,
        email=email,
        purpose=OTPPurpose.SIGNUP.value,
        expired=True,
    )

    create_pending_signup(
        session,
        email=email,
    )

    deleted_count = cleanup_expired_otps(
        session,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    assert deleted_count == 1

    assert otp is None

    assert pending_signup is None


def test_cleanup_deletes_expired_password_reset_otp_only(
    session,
):

    email = "passwordreset@example.com"

    create_otp(
        session,
        email=email,
        purpose=OTPPurpose.PASSWORD_RESET.value,
        expired=True,
    )

    deleted_count = cleanup_expired_otps(
        session,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert deleted_count == 1

    assert otp is None


def test_cleanup_preserves_non_expired_otp(
    session,
):

    email = "activeotp@example.com"

    create_otp(
        session,
        email=email,
        purpose=OTPPurpose.SIGNUP.value,
        expired=False,
    )

    deleted_count = cleanup_expired_otps(
        session,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert deleted_count == 0

    assert otp is not None


def test_cleanup_only_deletes_expired_otps(
    session,
):

    expired_email = "expired@example.com"

    active_email = "active@example.com"

    create_otp(
        session,
        email=expired_email,
        purpose=OTPPurpose.SIGNUP.value,
        expired=True,
    )

    create_otp(
        session,
        email=active_email,
        purpose=OTPPurpose.SIGNUP.value,
        expired=False,
    )

    deleted_count = cleanup_expired_otps(
        session,
    )

    expired_otp = session.exec(
        select(OTP).where(
            OTP.email == expired_email,
        )
    ).first()

    active_otp = session.exec(
        select(OTP).where(
            OTP.email == active_email,
        )
    ).first()

    assert deleted_count == 1

    assert expired_otp is None

    assert active_otp is not None


def test_cleanup_handles_missing_pending_signup_gracefully(
    session,
):

    email = "missingpending@example.com"

    create_otp(
        session,
        email=email,
        purpose=OTPPurpose.SIGNUP.value,
        expired=True,
    )

    deleted_count = cleanup_expired_otps(
        session,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert deleted_count == 1

    assert otp is None