import uuid

from argon2.exceptions import VerifyMismatchError
from fastapi import Form, HTTPException, Request, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.crud import get_user_by_login, get_user
from app.api.auth.utils_jwt import validate_password, decode_jwt
from app.models import User, db_helper


async def validate_auth_user(
    login=Form(),
    password=Form(),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> User:
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid login or password",
    )
    if not (user := await get_user_by_login(login, session=session)):
        raise unauthed_exc
    try:
        if not validate_password(
            password=password,
            hashed_password=user.password,
        ):
            raise unauthed_exc
    except VerifyMismatchError:
        raise unauthed_exc
    return user


async def get_user_by_token(
    request: Request,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> User:
    refresh_token = request.cookies.get("refresh_token")
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )
    try:
        payload = decode_jwt(refresh_token)
        subject = payload.get("sub")
        if subject:
            user_id = uuid.UUID(subject)
            return await get_user(user_id, session=session)
        raise unauthed_exc
    except:
        raise unauthed_exc
