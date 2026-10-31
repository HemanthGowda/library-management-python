from datetime import datetime

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.time import format_instant, utc_now

_VALUE_ERROR_PREFIX = "Value error, "

_MISSING_MESSAGES = {
    "email": "Email is required",
    "password": "Password is required",
    "fullName": "Full name is required",
    "title": "Title is required",
    "authorName": "Author name is required",
    "isbn": "ISBN is required",
    "publicationYear": "Publication year is required",
    "totalCopies": "Total copies is required",
    "availableCopies": "Available copies is required",
}


class FieldViolation(BaseModel):
    field: str
    message: str


class ApiError(BaseModel):
    timestamp: str
    status: int
    error: str
    message: str
    path: str
    violations: list[FieldViolation] | None = None


def error_payload(
    status: int,
    error: str,
    message: str,
    path: str,
    violations: list[dict[str, str]] | None = None,
    when: datetime | None = None,
) -> dict:
    body = {
        "timestamp": format_instant(when or utc_now()),
        "status": status,
        "error": error,
        "message": message,
        "path": path,
    }
    if violations:
        body["violations"] = violations
    return body


def error_response(
    status: int,
    error: str,
    message: str,
    path: str,
    violations: list[dict[str, str]] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=error_payload(status, error, message, path, violations),
    )


def violations_from_request(exc: RequestValidationError) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for err in exc.errors():
        field = _field_name(err.get("loc", ()))
        message = _message_for(field, err)
        violations.append({"field": field, "message": message})
    return violations


def is_malformed_json(exc: RequestValidationError) -> bool:
    return any(err.get("type") == "json_invalid" for err in exc.errors())


def _field_name(loc: tuple | list) -> str:
    parts = [str(part) for part in loc if part not in {"body", "query", "path"}]
    if not parts:
        return "request"
    return parts[-1]


def _message_for(field: str, err: dict) -> str:
    error_type = err.get("type", "")
    raw = str(err.get("msg", "Request validation failed"))
    if raw.startswith(_VALUE_ERROR_PREFIX):
        return raw[len(_VALUE_ERROR_PREFIX) :]
    if error_type in {"missing", "string_type", "int_type", "int_parsing"}:
        return _MISSING_MESSAGES.get(field, "Request validation failed")
    return raw


class ErrorResponses:
    bad_request = {400: {"model": ApiError, "description": "Validation failed"}}
    unauthorized = {401: {"model": ApiError, "description": "Missing or invalid token"}}
    forbidden = {403: {"model": ApiError, "description": "Insufficient role"}}
    not_found = {404: {"model": ApiError, "description": "Resource not found"}}
    conflict = {409: {"model": ApiError, "description": "Conflict"}}

