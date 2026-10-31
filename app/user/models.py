from dataclasses import dataclass
from datetime import datetime

ROLE_ORDER = ("ADMIN", "LIBRARIAN", "MEMBER")


def ordered_roles(roles: list[str] | set[str] | frozenset[str]) -> list[str]:
    present = set(roles)
    ordered = [role for role in ROLE_ORDER if role in present]
    extras = sorted(role for role in present if role not in ROLE_ORDER)
    return ordered + extras


@dataclass
class User:
    id: str | None
    email: str
    password_hash: str
    full_name: str
    roles: list[str]
    enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
