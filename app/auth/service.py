from app.auth.dto import LoginRequest, LoginResponse
from app.auth.jwt import JwtService
from app.auth.password import BcryptPasswordEncoder
from app.exception.errors import BadCredentialsException, DisabledException
from app.user.models import ordered_roles
from app.user.repository import UserRepository


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        password_encoder: BcryptPasswordEncoder,
        jwt_service: JwtService,
    ) -> None:
        self._users = users
        self._password_encoder = password_encoder
        self._jwt_service = jwt_service

    def login(self, request: LoginRequest) -> LoginResponse:
        email = request.email.strip().lower()
        user = self._users.find_by_email_ignore_case(email)
        if user is None:
            raise BadCredentialsException("Invalid email or password")
        if not user.enabled:
            raise DisabledException("Account is disabled")
        if not self._password_encoder.matches(request.password, user.password_hash):
            raise BadCredentialsException("Invalid email or password")

        roles = ordered_roles(user.roles)
        token = self._jwt_service.generate_token(user.id, user.email, roles)
        return LoginResponse(
            accessToken=token,
            tokenType="Bearer",
            expiresInMs=self._jwt_service.expiration_ms,
            userId=user.id,
            email=user.email,
            roles=roles,
        )
