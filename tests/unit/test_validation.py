import pytest
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.errors import violations_from_request
from app.book.dto import UpdateBookRequest
from app.user.dto import RegisterUserRequest


def _messages(model, payload: dict) -> dict[str, str]:
    with pytest.raises(ValidationError) as caught:
        model.model_validate(payload)
    violations = violations_from_request(RequestValidationError(caught.value.errors()))
    return {item["field"]: item["message"] for item in violations}


def test_register_rejects_invalid_payload():
    messages = _messages(
        RegisterUserRequest,
        {"email": "not-an-email", "password": "short", "fullName": ""},
    )
    assert messages["email"] == "Email must be valid"
    assert messages["password"] == "Password must be between 8 and 72 characters"
    assert messages["fullName"] == "Full name is required"


def test_book_update_rejects_hyphenated_isbn_and_copy_bounds():
    messages = _messages(
        UpdateBookRequest,
        {
            "title": "Title",
            "authorName": "Author",
            "isbn": "978-0134685991",
            "publicationYear": 1449,
            "totalCopies": 0,
            "availableCopies": -1,
        },
    )
    assert messages["isbn"] == "ISBN must be a valid ISBN-10 or ISBN-13 without hyphens"
    assert messages["publicationYear"] == "Publication year must be 1450 or later"
    assert messages["totalCopies"] == "Total copies must be at least 1"
    assert messages["availableCopies"] == "Available copies cannot be negative"
