from datetime import (
    datetime,
    timezone,
)

## FOR CODEBASE
def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


## FOR TESTING TO PREVENT SQLite SHIFTS
def get_naive_utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_utc_datetime(
    value: datetime,
) -> datetime:

    if value.tzinfo is None:

        return value.replace(
            tzinfo=timezone.utc,
        )

    return value
