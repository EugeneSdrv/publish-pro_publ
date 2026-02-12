import uuid

from fastapi import status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession,
) -> User:
    result = await session.scalars(select(User).where(User.user_id == user_id))
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid login or password",
        )
    await session.close()
    return user


async def get_user_by_login(
    login: str,
    session: AsyncSession,
) -> User:
    result = await session.scalars(select(User).where(User.login == login))
    user = result.first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid login or password",
        )
    await session.close()
    return user


