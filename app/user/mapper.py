from app.user.dto import UserResponse
from app.user.models import User, ordered_roles


def to_response(user: User) -> UserResponse:
    if user.id is None or user.created_at is None:
        raise RuntimeError("User must be persisted before it is returned")
    return UserResponse(
        id=user.id,
        email=user.email,
        fullName=user.full_name,
        roles=ordered_roles(user.roles),
        enabled=user.enabled,
        createdAt=user.created_at,
    )
