import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.api.time import format_instant

ISBN_PATTERN = re.compile(r"^(97[89])?\d{9}[\dXx]$")


class UpdateBookRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    authorName: str = Field(min_length=1, max_length=160)
    isbn: str = Field(pattern=r"^(97[89])?\d{9}[\dXx]$")
    description: str | None = Field(default=None, max_length=2000)
    publicationYear: int = Field(ge=1450, le=2100)
    totalCopies: int = Field(ge=1, le=10000)
    availableCopies: int = Field(ge=0, le=10000)

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: object) -> str:
        return _required_text(value, "Title is required", "Title must be between 1 and 200 characters", 1, 200)

    @field_validator("authorName", mode="before")
    @classmethod
    def validate_author_name(cls, value: object) -> str:
        return _required_text(
            value,
            "Author name is required",
            "Author name must be between 1 and 160 characters",
            1,
            160,
        )

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("ISBN is required")
        if ISBN_PATTERN.fullmatch(value) is None:
            raise ValueError("ISBN must be a valid ISBN-10 or ISBN-13 without hyphens")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Description must be at most 2000 characters")
        if len(value) > 2000:
            raise ValueError("Description must be at most 2000 characters")
        return value

    @field_validator("publicationYear", mode="before")
    @classmethod
    def validate_year(cls, value: object) -> int:
        return _required_int(
            value,
            "Publication year is required",
            "Publication year must be 1450 or later",
            "Publication year must be 2100 or earlier",
            1450,
            2100,
        )

    @field_validator("totalCopies", mode="before")
    @classmethod
    def validate_total_copies(cls, value: object) -> int:
        return _required_int(
            value,
            "Total copies is required",
            "Total copies must be at least 1",
            "Total copies must be at most 10000",
            1,
            10000,
        )

    @field_validator("availableCopies", mode="before")
    @classmethod
    def validate_available_copies(cls, value: object) -> int:
        return _required_int(
            value,
            "Available copies is required",
            "Available copies cannot be negative",
            "Available copies must be at most 10000",
            0,
            10000,
        )


class BookResponse(BaseModel):
    id: str
    title: str
    authorName: str
    isbn: str
    description: str | None = None
    publicationYear: int
    totalCopies: int
    availableCopies: int
    createdAt: datetime
    updatedAt: datetime

    @field_serializer("createdAt", "updatedAt")
    def serialize_timestamps(self, value: datetime) -> str:
        return format_instant(value)


def _required_text(value: object, required: str, size_message: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(required)
    if len(value) < minimum or len(value) > maximum:
        raise ValueError(size_message)
    return value


def _required_int(
    value: object,
    required: str,
    too_small: str,
    too_large: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(required)
    if value < minimum:
        raise ValueError(too_small)
    if value > maximum:
        raise ValueError(too_large)
    return value
