import random

from sqlmodel import Session

from app.core.constants.auth import PROFILE_COLORS

from app.services.auth.auth_validators import (
    normalize_username,
)

from app.services.auth.auth_queries import (
    is_username_taken,
)


def generate_profile_color() -> str:

    return random.choice(PROFILE_COLORS)


def generate_profile_initial(
    name: str | None,
) -> str:

    if not name:
        return "G"

    return name[0].upper()


def generate_username_suggestions(
    session: Session,
    name: str,
) -> list[str]:

    base_username = normalize_username(
        name.replace(
            " ",
            "",
        )
    )

    suggestions: list[str] = []

    if not is_username_taken(
        session,
        base_username,
    ):
        suggestions.append(base_username)

    while len(suggestions) < 5:

        random_number = random.randint(
            100,
            9999,
        )

        candidate = f"{base_username}{random_number}"

        if candidate not in suggestions and not is_username_taken(
            session,
            candidate,
        ):
            suggestions.append(candidate)

    return suggestions

def generate_available_username(
    session: Session,
    name: str,
) -> tuple[str, str]:

    suggestions = generate_username_suggestions(
        session,
        name,
    )

    username = suggestions[0]

    normalized_username = normalize_username(
        username,
    )

    return (
        username,
        normalized_username,
    )
