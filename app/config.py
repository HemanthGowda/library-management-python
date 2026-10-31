import os
from dataclasses import dataclass


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    server_port: int
    jwt_secret: str
    jwt_expiration_ms: int
    jwt_issuer: str
    seed_admin_email: str
    seed_admin_password: str
    seed_admin_full_name: str

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        return cls(
            mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017/library_management"),
            server_port=int(os.getenv("SERVER_PORT", "8080")),
            jwt_secret=os.getenv(
                "JWT_SECRET",
                "change-me-to-a-long-random-secret-at-least-32-chars",
            ),
            jwt_expiration_ms=int(os.getenv("JWT_EXPIRATION_MS", "3600000")),
            jwt_issuer=os.getenv("JWT_ISSUER", "library-management"),
            seed_admin_email=os.getenv("SEED_ADMIN_EMAIL", "admin@library.local"),
            seed_admin_password=os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!"),
            seed_admin_full_name=os.getenv("SEED_ADMIN_FULL_NAME", "Library Admin"),
        )
