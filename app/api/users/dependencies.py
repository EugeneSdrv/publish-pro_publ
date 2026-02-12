import uuid

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from  jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.utils_jwt import decode_jwt
from app.api.users.crud import get_user
from app.models import db_helper

required_auth = HTTPBearer(auto_error=True)

async def get_user_by_access(
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    try:
        token = creds.credentials
        payload = decode_jwt(token)
        user_id = uuid.UUID(payload.get("sub"))
        return await get_user(user_id, session=session)
    except (ExpiredSignatureError, InvalidTokenError) as e:
        raise HTTPException(
            # TODO: нужно ли расшифровывать ошибки
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"unauthorized because of {e}",
        )
