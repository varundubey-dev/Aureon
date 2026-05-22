from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.auth.otp import OTP
from app.models.auth.pending_signup import PendingSignup

from app.core.enums import OTPPurpose


def cleanup_expired_otps(
    session: Session,
) -> int:

    now = datetime.now(
        timezone.utc,
    )

    expired_otps = session.exec(
        select(OTP).where(
            OTP.expires_at < now,
        ),
    ).all()

    deleted_count = 0

    for otp in expired_otps:

        if otp.purpose == OTPPurpose.SIGNUP.value:

            pending_signup = session.exec(
                select(PendingSignup).where(
                    PendingSignup.email == otp.email,
                ),
            ).first()

            if pending_signup:

                session.delete(
                    pending_signup,
                )

        session.delete(
            otp,
        )

        deleted_count += 1

    session.commit()

    return deleted_count
