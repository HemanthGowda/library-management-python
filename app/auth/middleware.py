from starlette.datastructures import Headers, State
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.errors import error_response
from app.auth.jwt import JwtError
from app.auth.principal import Principal

_PUBLIC_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/users"),
    ("GET", "/actuator/health"),
    ("GET", "/actuator/info"),
}


class AuthenticationMiddleware:
    def __init__(self, app: ASGIApp, fastapi_app) -> None:
        self.app = app
        self.fastapi_app = fastapi_app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "")
        headers = Headers(scope=scope)
        principal = self._principal_from_header(headers.get("authorization"))
        state = scope.get("state")
        if not isinstance(state, State):
            state = State()
            scope["state"] = state
        state.principal = principal

        if principal is None and not _is_public(method, path):
            response = error_response(
                401,
                "Unauthorized",
                "Authentication is required",
                path,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _principal_from_header(self, header: str | None) -> Principal | None:
        if header is None or not header.startswith("Bearer "):
            return None
        token = header[len("Bearer ") :].strip()
        if not token:
            return None
        jwt_service = getattr(self.fastapi_app.state, "jwt_service", None)
        if jwt_service is None:
            return None
        try:
            claims = jwt_service.parse_claims(token)
            roles = jwt_service.extract_roles(claims)
            email = claims.get("email")
            subject = claims.get("sub")
            if not isinstance(subject, str) or not isinstance(email, str):
                return None
            return Principal(user_id=subject, email=email, roles=frozenset(roles))
        except (JwtError, ValueError):
            return None


def _is_public(method: str, path: str) -> bool:
    if (method, path) in _PUBLIC_ROUTES:
        return True
    if method != "GET":
        return False
    return (
        path == "/v3/api-docs"
        or path.startswith("/v3/api-docs/")
        or path == "/swagger-ui.html"
        or path.startswith("/swagger-ui")
    )
