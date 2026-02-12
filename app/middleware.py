import uuid

import jwt
from fastapi import Request, status
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.auth.utils_jwt import decode_jwt


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._required_auth = HTTPBearer(auto_error=False)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)
        token = await self._required_auth(request)
        if token:
            try:
                payload = decode_jwt(token.credentials)
                user_id = payload.get("sub")
                request.state.user_id = uuid.UUID(user_id)
                user_role = payload.get("role")
                request.state.user_role = user_role
            except (HTTPException, jwt.InvalidTokenError, jwt.ExpiredSignatureError):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Not authenticated",
                        "headers": {"WWW-Authenticate": "Bearer"},
                    },
                )
        else:
            request.state.user_id = None
            request.state.user_role = None

        response = await call_next(request)
        return response
