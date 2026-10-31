import pytest

from app.auth.dto import LoginRequest
from app.auth.jwt import JwtService
from app.auth.service import AuthService
from app.exception.errors import BadCredentialsException, DisabledException
from app.user.models import User


class FakeUsers:
    def __init__(self, user: User | None = None) -> None:
        self.user = user

    def find_by_email_ignore_case(self, email: str) -> User | None:
        if self.user is not None and self.user.email == email:
            return self.user
        return None


class FakeEncoder:
    def encode(self, raw_password: str) -> str:
        return "hashed"

    def matches(self, raw_password: str, encoded_password: str) -> bool:
        return encoded_password == "hashed" and raw_password == "ChangeMe123!"


def _service(user: User | None = None) -> AuthService:
    return AuthService(
        FakeUsers(user),
        FakeEncoder(),
        JwtService(
            "test-secret-key-that-is-long-enough-for-hs256-signing",
            3_600_000,
            "library-management-test",
        ),
    )


def _admin(enabled: bool = True) -> User:
    return User(
        id="admin-1",
        email="admin@library.local",
        password_hash="hashed",
        full_name="Library Admin",
        roles=["ADMIN"],
        enabled=enabled,
    )


def test_login_returns_bearer_token_for_valid_credentials():
    response = _service(_admin()).login(LoginRequest(email="admin@library.local", password="ChangeMe123!"))

    assert response.tokenType == "Bearer"
    assert response.accessToken
    assert response.email == "admin@library.local"
    assert response.roles == ["ADMIN"]
    assert response.expiresInMs == 3_600_000
    assert response.userId == "admin-1"


def test_login_rejects_unknown_user():
    with pytest.raises(BadCredentialsException):
        _service().login(LoginRequest(email="missing@library.local", password="Password1"))


def test_login_rejects_disabled_account():
    with pytest.raises(DisabledException):
        _service(_admin(enabled=False)).login(
            LoginRequest(email="admin@library.local", password="ChangeMe123!")
        )


def test_login_rejects_invalid_password():
    with pytest.raises(BadCredentialsException):
        _service(_admin()).login(LoginRequest(email="admin@library.local", password="wrong"))
