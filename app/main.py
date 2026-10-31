import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

from app.api.errors import error_response, is_malformed_json, violations_from_request
from app.auth.jwt import JwtService
from app.auth.middleware import AuthenticationMiddleware
from app.auth.password import BcryptPasswordEncoder
from app.auth.router import router as auth_router
from app.auth.service import AuthService
from app.book.repository import BookRepository
from app.book.router import router as book_router
from app.book.service import BookService
from app.config import Settings
from app.exception.errors import (
    BadCredentialsException,
    BadRequestException,
    ConflictException,
    DisabledException,
    ForbiddenException,
    ResourceNotFoundException,
)
from app.health import router as health_router
from app.migration.runner import run_migrations
from app.user.repository import UserRepository
from app.user.router import router as user_router
from app.user.service import UserService

logger = logging.getLogger("library")
logging.basicConfig(level=logging.INFO)

OPENAPI_DESCRIPTION = """
Half-baked library management backend for intern onboarding.

Fully implemented reference slices:
- POST /api/v1/users — public member registration
- POST /api/v1/auth/login — JWT login
- PUT /api/v1/books/{id} — secured book update (ADMIN, LIBRARIAN)

The Author resource is intentionally left unimplemented for interns.
""".strip()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = MongoClient(resolved.mongodb_uri, tz_aware=True, serverSelectionTimeoutMS=5000)
        database = client[_database_name(resolved.mongodb_uri)]
        encoder = BcryptPasswordEncoder()
        run_migrations(database, resolved, encoder)
        jwt_service = JwtService(resolved.jwt_secret, resolved.jwt_expiration_ms, resolved.jwt_issuer)
        users = UserRepository(database["users"])
        books = BookRepository(database["books"])
        app.state.settings = resolved
        app.state.mongo_client = client
        app.state.db = database
        app.state.password_encoder = encoder
        app.state.jwt_service = jwt_service
        app.state.user_service = UserService(users, encoder)
        app.state.auth_service = AuthService(users, encoder, jwt_service)
        app.state.book_service = BookService(books)
        try:
            yield
        finally:
            client.close()

    app = FastAPI(
        title="Library Management API",
        version="0.1.0",
        description=OPENAPI_DESCRIPTION,
        docs_url="/swagger-ui.html",
        openapi_url="/v3/api-docs",
        redoc_url=None,
        lifespan=lifespan,
        redirect_slashes=False,
    )
    app.include_router(health_router)
    app.include_router(user_router)
    app.include_router(auth_router)
    app.include_router(book_router)
    _register_exception_handlers(app)
    app.openapi = lambda: _openapi(app)
    app.add_middleware(AuthenticationMiddleware, fastapi_app=app)
    return app


def _database_name(uri: str) -> str:
    parsed = parse_uri(uri)
    return parsed.get("database") or "library_management"


def _openapi(app: FastAPI) -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["info"]["contact"] = {
        "name": "Library Engineering",
        "email": "engineering@library.local",
    }
    components = schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "name": "bearerAuth",
    }
    app.openapi_schema = schema
    return schema


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError):
        if is_malformed_json(exc):
            return error_response(
                400,
                "Malformed JSON",
                "Request body could not be parsed",
                request.url.path,
            )
        return error_response(
            400,
            "Validation Failed",
            "Request validation failed",
            request.url.path,
            violations_from_request(exc),
        )

    @app.exception_handler(BadRequestException)
    async def handle_bad_request(request: Request, exc: BadRequestException):
        return error_response(400, "Bad Request", str(exc), request.url.path)

    @app.exception_handler(ResourceNotFoundException)
    async def handle_not_found(request: Request, exc: ResourceNotFoundException):
        return error_response(404, "Not Found", str(exc), request.url.path)

    @app.exception_handler(ConflictException)
    async def handle_conflict(request: Request, exc: ConflictException):
        return error_response(409, "Conflict", str(exc), request.url.path)

    @app.exception_handler(BadCredentialsException)
    @app.exception_handler(DisabledException)
    async def handle_auth_failure(request: Request, exc: Exception):
        return error_response(401, "Unauthorized", str(exc), request.url.path)

    @app.exception_handler(ForbiddenException)
    async def handle_forbidden(request: Request, exc: ForbiddenException):
        return error_response(
            403,
            "Forbidden",
            "You do not have permission to perform this action",
            request.url.path,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return error_response(
            500,
            "Internal Server Error",
            "An unexpected error occurred",
            request.url.path,
        )


app = create_app()
