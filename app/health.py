from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


@router.get("/actuator/health", summary="Health check")
def health(request: Request):
    database = getattr(request.app.state, "db", None)
    if database is None:
        return JSONResponse(status_code=503, content={"status": "DOWN"})
    try:
        database.command("ping")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "DOWN"})
    return {"status": "UP"}


@router.get("/actuator/info", summary="Application info")
def info() -> dict:
    return {"app": {"name": "library-management"}}
