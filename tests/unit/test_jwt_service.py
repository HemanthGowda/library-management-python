import base64

import pytest

from app.auth.jwt import JwtService


SECRET = "test-secret-key-that-is-long-enough-for-hs256-signing"


def test_generate_and_parse_token_round_trip():
    service = JwtService(SECRET, 3_600_000, "library-management-test")
    token = service.generate_token("user-42", "admin@library.local", ["LIBRARIAN", "ADMIN"])
    claims = service.parse_claims(token)

    assert claims["sub"] == "user-42"
    assert claims["email"] == "admin@library.local"
    assert service.extract_roles(claims) == {"ADMIN", "LIBRARIAN"}
    assert service.expiration_ms == 3_600_000


def test_accepts_base64_secret():
    encoded = base64.b64encode(b"x" * 32).decode("ascii")
    service = JwtService(encoded, 1000, "library-management")
    token = service.generate_token("user-1", "reader@example.com", ["MEMBER"])
    claims = service.parse_claims(token)
    assert claims["sub"] == "user-1"


def test_rejects_short_secret():
    with pytest.raises(RuntimeError, match="256 bits"):
        JwtService("too-short", 1000, "issuer")
