from fastapi import APIRouter, Request

from app.api.errors import ErrorResponses
from app.user.dto import RegisterUserRequest, UserResponse

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post(
    "",
    status_code=201,
    response_model=UserResponse,
    summary="Register a new member",
    description="Public endpoint that creates a MEMBER account. Email must be unique.",
    responses={
        **ErrorResponses.bad_request,
        **ErrorResponses.conflict,
    },
)
def register(body: RegisterUserRequest, request: Request) -> UserResponse:
    return request.app.state.user_service.register(body)
