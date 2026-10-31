import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.api.time import format_instant
from app.auth.dto import EMAIL_PATTERN

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(max_length=255, json_schema_extra={"format": "email"})
    password: str = Field(
        min_length=8,
        max_length=72,
        json_schema_extra={"pattern": r"^(?=.*[A-Za-z])(?=.*\d).+$"},
    )
    fullName: str = Field(min_length=2, max_length=120)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("Email is required")
        if len(value) > 255:
            raise ValueError("Email must be at most 255 characters")
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Email must be valid")
        return value

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("Password is required")
        if len(value) < 8 or len(value) > 72:
            raise ValueError("Password must be between 8 and 72 characters")
        if PASSWORD_PATTERN.fullmatch(value) is None:
            raise ValueError("Password must contain at least one letter and one number")
        return value

    @field_validator("fullName", mode="before")
    @classmethod
    def validate_full_name(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("Full name is required")
        if len(value) < 2 or len(value) > 120:
            raise ValueError("Full name must be between 2 and 120 characters")
        return value


class UserResponse(BaseModel):
    id: str
    email: str
    fullName: str
    roles: list[str]
    enabled: bool
    createdAt: datetime

    @field_serializer("createdAt")
    def serialize_created_at(self, value: datetime) -> str:
        return format_instant(value)
