from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.utils_jwt import decode_jwt
from app.models import JWTSession


async def create_jwt_session(
    user,
    refresh_token,
    session: AsyncSession,
):
    refresh_payload = decode_jwt(refresh_token, options={"verify_signature": False})
    new_jwt_session = JWTSession(
        user_id=user.user_id,
        token=refresh_token,
        created_at=datetime.now(),
        token_id=refresh_payload.get("jti"),
        expires_in=datetime.fromtimestamp(refresh_payload.get("exp")),
    )
    statement = select(JWTSession).where(JWTSession.user_id == user.user_id)
    if current_refresh_session := await session.scalar(statement):
        await session.delete(current_refresh_session)
        await session.commit()
    session.add(new_jwt_session)
    await session.commit()
    return await session.close()


async def update_jwt_session(
    refresh,
    request,
    session: AsyncSession,
):
    current_token = request.cookies.get("refresh_token")
    current_refresh_payload = decode_jwt(current_token)
    current_token_id = current_refresh_payload.get("jti")
    statement = select(JWTSession).where(JWTSession.token_id == current_token_id)
    # возможно стоит сделать индекс на JWTSession.token_id для ускорения поиска
    if current_jwt_session := await session.scalar(statement):
        new_refresh_payload = decode_jwt(refresh, options={"verify_signature": False})
        current_jwt_session.token = refresh
        current_jwt_session.created_at = datetime.now()
        current_jwt_session.token_id = new_refresh_payload.get("jti")
        current_jwt_session.expires_in = datetime.fromtimestamp(new_refresh_payload.get("exp"))
        session.add(current_jwt_session)
        await session.commit()


async def delete_jwt_session(
    session: AsyncSession,
    request,
):
    current_token = request.cookies.get("refresh_token")
    current_refresh_payload = decode_jwt(current_token)
    current_token_id = current_refresh_payload.get("jti")
    statement = select(JWTSession).where(JWTSession.token_id == current_token_id)
    # возможно стоит сделать индекс на JWTSession.token_id для ускорения поиска
    if current_refresh_session := await session.scalar(statement):
        await session.delete(current_refresh_session)
        await session.commit()
