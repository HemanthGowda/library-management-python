from app.auth.password import BcryptPasswordEncoder
from app.exception.errors import ConflictException
from app.user.dto import RegisterUserRequest, UserResponse
from app.user.mapper import to_response
from app.user.models import User
from app.user.repository import UserRepository


class UserService:
    def __init__(self, users: UserRepository, password_encoder: BcryptPasswordEncoder) -> None:
        self._users = users
        self._password_encoder = password_encoder

    def register(self, request: RegisterUserRequest) -> UserResponse:
        email = request.email.strip().lower()
        if self._users.exists_by_email_ignore_case(email):
            raise ConflictException("Email is already registered")

        user = User(
            id=None,
            email=email,
            password_hash=self._password_encoder.encode(request.password),
            full_name=request.fullName.strip(),
            roles=["MEMBER"],
            enabled=True,
        )
        saved = self._users.save(user)
        return to_response(saved)
