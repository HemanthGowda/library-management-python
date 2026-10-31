from datetime import datetime, timezone

from app.user.dto import RegisterUserRequest
from app.user.models import User
from app.user.service import UserService
from app.exception.errors import ConflictException
import pytest


class FakeUsers:
    def __init__(self, existing: set[str] | None = None) -> None:
        self.existing = existing or set()
        self.saved: User | None = None

    def exists_by_email_ignore_case(self, email: str) -> bool:
        return email in self.existing

    def save(self, user: User) -> User:
        user.id = "user-1"
        user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        user.updated_at = user.created_at
        self.saved = user
        return user


class FakeEncoder:
    def encode(self, raw_password: str) -> str:
        return "hashed"

    def matches(self, raw_password: str, encoded_password: str) -> bool:
        return False


def test_register_creates_member_with_normalized_email():
    users = FakeUsers()
    service = UserService(users, FakeEncoder())
    request = RegisterUserRequest.model_construct(
        email="  Alex@Example.com ",
        password="Password1",
        fullName=" Alex Reader ",
    )

    response = service.register(request)

    assert users.saved is not None
    assert users.saved.email == "alex@example.com"
    assert users.saved.full_name == "Alex Reader"
    assert users.saved.password_hash == "hashed"
    assert users.saved.roles == ["MEMBER"]
    assert users.saved.enabled is True
    assert response.id == "user-1"
    assert response.email == "alex@example.com"
    assert response.roles == ["MEMBER"]


def test_register_rejects_duplicate_email():
    users = FakeUsers({"alex@example.com"})
    service = UserService(users, FakeEncoder())
    request = RegisterUserRequest.model_construct(
        email="Alex@Example.com",
        password="Password1",
        fullName="Alex Reader",
    )

    with pytest.raises(ConflictException, match="Email is already registered"):
        service.register(request)
