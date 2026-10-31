from fastapi import APIRouter, Depends, Request

from app.api.errors import ErrorResponses
from app.auth.principal import Principal
from app.book.dto import BookResponse, UpdateBookRequest
from app.exception.errors import ForbiddenException

router = APIRouter(prefix="/api/v1/books", tags=["Books"])


def require_catalog_manager(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if principal is None or not principal.has_any_role("ADMIN", "LIBRARIAN"):
        raise ForbiddenException("You do not have permission to perform this action")
    return principal


@router.put(
    "/{id}",
    response_model=BookResponse,
    response_model_exclude_none=True,
    summary="Update a book",
    description="Fully replaces mutable book fields. Requires ADMIN or LIBRARIAN role.",
    responses={
        **ErrorResponses.bad_request,
        **ErrorResponses.unauthorized,
        **ErrorResponses.forbidden,
        **ErrorResponses.not_found,
        **ErrorResponses.conflict,
    },
    openapi_extra={"security": [{"bearerAuth": []}]},
)
def update_book(
    id: str,
    body: UpdateBookRequest,
    request: Request,
    _: Principal = Depends(require_catalog_manager),
) -> BookResponse:
    return request.app.state.book_service.update(id, body)
