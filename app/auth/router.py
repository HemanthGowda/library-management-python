from fastapi import APIRouter, Request

from app.api.errors import ErrorResponses
from app.auth.dto import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login",
    description="Authenticate with email and password to receive a JWT access token.",
    responses={
        **ErrorResponses.bad_request,
        401: {"description": "Invalid credentials"},
    },
)
def login(body: LoginRequest, request: Request) -> LoginResponse:
    return request.app.state.auth_service.login(body)
