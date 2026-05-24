# =========================================================
# Scheduler Tests
# =========================================================
#
# This file tests:
#
# scheduler.py
#
# Covered areas:
#
# 1. Cleanup runner execution
#    - OTP cleanup runner
#    - Refresh session cleanup runner
#    - Guest cleanup runner
#
# 2. Scheduler startup
#    - Job registration
#    - Immediate cleanup execution
#    - Duplicate startup prevention
#
# 3. Scheduler shutdown
#    - Graceful shutdown
#
# NOTE:
#
# - APScheduler internals are NOT tested.
# - Timing behavior is NOT tested.
# - This file tests ONLY orchestration behavior.
#
# =========================================================

from unittest.mock import (
    MagicMock,
    patch,
)

from app.services.maintenance import scheduler

# =========================================================
# Cleanup Runners
# =========================================================


@patch(
    "app.services.maintenance.scheduler.cleanup_expired_otps",
)
def test_run_otp_cleanup(
    mock_cleanup,
):

    mock_cleanup.return_value = 5

    scheduler.run_otp_cleanup()

    assert mock_cleanup.called


@patch(
    "app.services.maintenance.scheduler.cleanup_expired_refresh_sessions",
)
def test_run_refresh_session_cleanup(
    mock_cleanup,
):

    mock_cleanup.return_value = {
        "deleted_sessions": 3,
        "deleted_guests": 1,
    }

    scheduler.run_refresh_session_cleanup()

    assert mock_cleanup.called


@patch(
    "app.services.maintenance.scheduler.cleanup_inactive_guest_accounts",
)
def test_run_guest_cleanup(
    mock_cleanup,
):

    mock_cleanup.return_value = 2

    scheduler.run_guest_cleanup()

    assert mock_cleanup.called


# =========================================================
# Scheduler Startup
# =========================================================


@patch(
    "app.services.maintenance.scheduler.run_guest_cleanup",
)
@patch(
    "app.services.maintenance.scheduler.run_refresh_session_cleanup",
)
@patch(
    "app.services.maintenance.scheduler.run_otp_cleanup",
)
@patch(
    "app.services.maintenance.scheduler.BackgroundScheduler",
)
def test_start_scheduler_registers_jobs(
    mock_scheduler_class,
    mock_otp_cleanup,
    mock_refresh_cleanup,
    mock_guest_cleanup,
):

    mock_scheduler = MagicMock()

    mock_scheduler.running = False

    mock_scheduler_class.return_value = mock_scheduler

    scheduler.scheduler = None

    scheduler.start_scheduler()

    assert mock_otp_cleanup.called

    assert mock_refresh_cleanup.called

    assert mock_guest_cleanup.called

    assert mock_scheduler.add_job.call_count == 3

    assert mock_scheduler.start.called


@patch(
    "app.services.maintenance.scheduler.BackgroundScheduler",
)
def test_start_scheduler_prevents_duplicate_start(
    mock_scheduler_class,
):

    existing_scheduler = MagicMock()

    existing_scheduler.running = True

    scheduler.scheduler = existing_scheduler

    scheduler.start_scheduler()

    assert not mock_scheduler_class.called


# =========================================================
# Scheduler Shutdown
# =========================================================


def test_stop_scheduler_shutdowns_running_scheduler():

    mock_scheduler = MagicMock()

    mock_scheduler.running = True

    scheduler.scheduler = mock_scheduler

    scheduler.stop_scheduler()

    assert mock_scheduler.shutdown.called


def test_stop_scheduler_ignores_missing_scheduler():

    scheduler.scheduler = None

    scheduler.stop_scheduler()


def test_stop_scheduler_ignores_stopped_scheduler():

    mock_scheduler = MagicMock()

    mock_scheduler.running = False

    scheduler.scheduler = mock_scheduler

    scheduler.stop_scheduler()

    assert not mock_scheduler.shutdown.called
