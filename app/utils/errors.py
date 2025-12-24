from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id")
        request.state.request_id = rid or f"req_{uuid.uuid4().hex[:12]}"
        response = await call_next(request)
        response.headers["x-request-id"] = request.state.request_id
        return response

async def global_exception_handler(request: Request, exc: Exception):
    rid = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc), "request_id": rid},
    )
