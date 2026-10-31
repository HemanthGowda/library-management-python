import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(json_schema_extra={"format": "email"})
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("Email is required")
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Email must be valid")
        return value

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: object) -> str:
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError("Password is required")
        return value


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str
    expiresInMs: int
    userId: str
    email: str
    roles: list[str]
