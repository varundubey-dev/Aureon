from apscheduler.schedulers.background import (
    BackgroundScheduler,
)

from sqlmodel import Session

from app.core.database import engine

from app.services.maintenance.otp_cleanup import (
    cleanup_expired_otps,
)

from app.services.maintenance.session_cleanup import (
    cleanup_expired_refresh_sessions,
)

from app.services.maintenance.guest_cleanup import (
    cleanup_inactive_guest_accounts,
)

scheduler = None


def run_otp_cleanup():

    print("Running OTP cleanup...")

    with Session(engine) as session:

        deleted = cleanup_expired_otps(
            session,
        )

    print(f"Deleted {deleted} expired OTP records")


def run_refresh_session_cleanup():

    print("Running refresh session cleanup...")

    with Session(engine) as session:

        result = cleanup_expired_refresh_sessions(
            session,
        )

    print(
        f"Deleted {result['deleted_sessions']} expired refresh sessions",
    )

    print(
        f"Deleted {result['deleted_guests']} guest accounts",
    )


def run_guest_cleanup():

    print("Running inactive guest cleanup...")

    with Session(engine) as session:

        deleted = cleanup_inactive_guest_accounts(
            session,
        )

    print(f"Deleted {deleted} inactive guest accounts")


def start_scheduler():

    global scheduler

    if scheduler and scheduler.running:
        return

    scheduler = BackgroundScheduler()

    # Run immediately on startup
    run_otp_cleanup()
    run_refresh_session_cleanup()
    run_guest_cleanup()

    # Every 15 minutes
    scheduler.add_job(
        run_otp_cleanup,
        trigger="interval",
        minutes=15,
    )

    # Every 2 hours
    scheduler.add_job(
        run_refresh_session_cleanup,
        trigger="interval",
        hours=2,
    )

    # Every 12 hours
    scheduler.add_job(
        run_guest_cleanup,
        trigger="interval",
        hours=12,
    )

    scheduler.start()

    print("Maintenance scheduler started")


def stop_scheduler():

    global scheduler

    if scheduler and scheduler.running:

        scheduler.shutdown()

        print("Maintenance scheduler stopped")