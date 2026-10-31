import base64
from datetime import timedelta

import jwt

from app.api.time import utc_now


class JwtError(Exception):
    pass


class JwtService:
    def __init__(self, secret: str, expiration_ms: int, issuer: str) -> None:
        key = decode_secret(secret)
        if len(key) < 32:
            raise RuntimeError("JWT secret must be at least 256 bits (32 bytes)")
        self._key = key
        self.expiration_ms = expiration_ms
        self.issuer = issuer

    def generate_token(self, user_id: str, email: str, roles: list[str]) -> str:
        now = utc_now()
        expires_at = now + timedelta(milliseconds=self.expiration_ms)
        payload = {
            "iss": self.issuer,
            "sub": user_id,
            "email": email,
            "roles": list(roles),
            "iat": now,
            "exp": expires_at,
        }
        token = jwt.encode(payload, self._key, algorithm="HS256")
        if isinstance(token, bytes):
            return token.decode("utf-8")
        return token

    def parse_claims(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self._key,
                algorithms=["HS256"],
                issuer=self.issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise JwtError(str(exc)) from exc

    def extract_roles(self, claims: dict) -> set[str]:
        raw = claims.get("roles")
        if not isinstance(raw, list):
            return set()
        roles: set[str] = set()
        for item in raw:
            name = str(item)
            if name not in {"ADMIN", "LIBRARIAN", "MEMBER"}:
                raise ValueError(f"Unknown role: {name}")
            roles.add(name)
        return roles


def decode_secret(secret: str) -> bytes:
    try:
        return base64.b64decode(secret, validate=True)
    except Exception:
        return secret.encode("utf-8")
