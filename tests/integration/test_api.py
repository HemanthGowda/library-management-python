import shutil
import subprocess
import uuid

import pytest

from app.api.time import utc_now
from app.config import Settings

pytestmark = pytest.mark.integration

_UPDATE = {
    "title": "Updated Seed Book",
    "authorName": "Updated Author",
    "isbn": "9780596009205",
    "description": "Updated by integration test",
    "publicationYear": 2021,
    "totalCopies": 6,
    "availableCopies": 5,
}


def _docker_ready() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _uri_with_database(url: str, database: str) -> str:
    query = ""
    if "?" in url:
        url, query = url.split("?", 1)
        query = "&" + query
    if url.endswith("/"):
        url = url[:-1]
    scheme, remainder = url.split("://", 1)
    if "/" in remainder:
        host, _current = remainder.rsplit("/", 1)
        base = f"{scheme}://{host}/{database}"
    else:
        base = f"{url}/{database}"
    return f"{base}?authSource=admin{query}"


@pytest.fixture(scope="module")
def api():
    if not _docker_ready():
        pytest.skip("Docker is required for integration tests")
    from fastapi.testclient import TestClient
    from testcontainers.community.mongodb import MongoDbContainer

    from app.main import create_app

    with MongoDbContainer("mongo:7.0") as mongo:
        settings = Settings(
            mongodb_uri=_uri_with_database(mongo.get_connection_url(), "library_management_test"),
            server_port=8080,
            jwt_secret="test-secret-key-that-is-long-enough-for-hs256-signing",
            jwt_expiration_ms=3_600_000,
            jwt_issuer="library-management-test",
            seed_admin_email="admin@library.local",
            seed_admin_password="ChangeMe123!",
            seed_admin_full_name="Library Admin",
        )
        application = create_app(settings)
        with TestClient(application) as client:
            yield client, application


@pytest.fixture(autouse=True)
def seed(api):
    client, application = api
    database = application.state.db
    encoder = application.state.password_encoder
    database.users.delete_many({})
    database.books.delete_many({})
    now = utc_now()
    database.users.insert_many(
        [
            {
                "email": "admin@library.local",
                "passwordHash": encoder.encode("ChangeMe123!"),
                "fullName": "Library Admin",
                "roles": ["ADMIN"],
                "enabled": True,
                "createdAt": now,
                "updatedAt": now,
            },
            {
                "email": "member@library.local",
                "passwordHash": encoder.encode("MemberPass1"),
                "fullName": "Library Member",
                "roles": ["MEMBER"],
                "enabled": True,
                "createdAt": now,
                "updatedAt": now,
            },
        ]
    )
    inserted = database.books.insert_one(
        {
            "title": "Seed Book",
            "authorName": "Seed Author",
            "isbn": "9780134685991",
            "description": "A seeded book",
            "publicationYear": 2018,
            "totalCopies": 3,
            "availableCopies": 3,
            "createdAt": now,
            "updatedAt": now,
        }
    )
    return {"client": client, "book_id": str(inserted.inserted_id)}


def _login(client, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"]
    assert body["tokenType"] == "Bearer"
    return body["accessToken"]


def test_register_login_and_update_book_happy_path(seed):
    client = seed["client"]
    email = f"intern+{uuid.uuid4()}@library.local"
    created = client.post(
        "/api/v1/users",
        json={"email": email, "password": "InternPass1", "fullName": "New Intern"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == email
    assert body["fullName"] == "New Intern"
    assert body["roles"] == ["MEMBER"]
    assert body["enabled"] is True
    assert "password" not in body
    assert "passwordHash" not in body

    token = _login(client, "admin@library.local", "ChangeMe123!")
    updated = client.put(
        f"/api/v1/books/{seed['book_id']}",
        headers={"Authorization": f"Bearer {token}"},
        json=_UPDATE,
    )
    assert updated.status_code == 200
    book = updated.json()
    assert book["title"] == "Updated Seed Book"
    assert book["isbn"] == "9780596009205"
    assert book["availableCopies"] == 5
    assert "createdAt" in book
    assert "updatedAt" in book


def test_register_rejects_invalid_payload(seed):
    response = seed["client"].post(
        "/api/v1/users",
        json={"email": "not-an-email", "password": "short", "fullName": ""},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "Validation Failed"
    assert isinstance(body["violations"], list)
    assert body["violations"]


def test_update_book_requires_authentication(seed):
    response = seed["client"].put(f"/api/v1/books/{seed['book_id']}", json=_UPDATE)
    assert response.status_code == 401
    assert response.json()["message"] == "Authentication is required"


def test_update_book_forbids_member_role(seed):
    token = _login(seed["client"], "member@library.local", "MemberPass1")
    response = seed["client"].put(
        f"/api/v1/books/{seed['book_id']}",
        headers={"Authorization": f"Bearer {token}"},
        json=_UPDATE,
    )
    assert response.status_code == 403
    assert response.json()["message"] == "You do not have permission to perform this action"


def test_login_rejects_bad_password(seed):
    response = seed["client"].post(
        "/api/v1/auth/login",
        json={"email": "admin@library.local", "password": "WrongPassword1"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"


def test_health_and_openapi_are_public(seed):
    client = seed["client"]
    health = client.get("/actuator/health")
    assert health.status_code == 200
    assert health.json()["status"] == "UP"
    docs = client.get("/v3/api-docs")
    assert docs.status_code == 200
    assert docs.json()["info"]["title"] == "Library Management API"
    swagger = client.get("/swagger-ui.html")
    assert swagger.status_code == 200
