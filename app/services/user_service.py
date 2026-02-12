import os
import re

from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.auth.utils_jwt import hash_password, validate_password
from app.api.users import schemas
from app.api.images.crud import delete_image
from app.services import create_image, S3ImageManager
from app.models import User, db_helper, UserRole



async def create_user(
    user_in: schemas.UserCreate,
    session: AsyncSession,
    client,
) -> User:
    if await session.scalar(
        select(User).where(User.login == user_in.login)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            # TODO: возможно стоит изменить detail
            detail={"login": f"A author with login {user_in.login} already exists"},
        )
    if await session.scalar(
        select(User).where(User.email == user_in.email)
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            # TODO: возможно стоит изменить detail
            detail={"email": f"The author with email {user_in.email} already exists"},
        )
    check_password_complexity(user_in.password)
    new_author = User(**user_in.model_dump(exclude={"profile_image"}))
    new_author.password = hash_password(user_in.password)
    session.add(new_author)
    await session.flush()
    if user_in.profile_image:
        storage = S3ImageManager("users-avatar-images", client)
        new_author.image = await create_image(user_in.profile_image, session, storage, new_author)
        new_author.profile_image = new_author.image.image_key
    session.add(new_author)
    await session.commit()
    return new_author


async def user_update(
    user_in,
    user,
    session: AsyncSession,
    client
):
    try:
        validate_password(
            password=user_in.password,
            hashed_password=user.password,
        )
    except VerifyMismatchError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )
    for field, value in user_in.model_dump(exclude_unset=True, exclude="password").items():
        if field == "profile_image" and value:
            storage = S3ImageManager("users-avatar-images", client)
            if image_key := user.profile_image:
                await storage.delete_object(image_key)
                await delete_image(user.profile_image, session, user)
            # TODO: в каком случае стоит удалять изображение или стоит это указывать параметром???
            user.image = await create_image(user_in.profile_image, session, storage, user)
            setattr(user, field, user.image.image_key)
        elif value:
            setattr(user, field, value)
    session.add(user)
    await session.commit()
    return user


def check_password_complexity(value):
    regex = r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).*$"
    if not re.match(regex, value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A password must contain at least one uppercase letter, one lowercase letter,\
        one digit, and one special character and must be between 8 and 32 characters long",
        )
    return value


async def user_password_update(user_password_in, user, session: AsyncSession):
    check_password_complexity(user_password_in.new_password)
    try:
        validate_password(
            password=user_password_in.current_password,
            hashed_password=user.password,
        )
    except VerifyMismatchError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )
    user.password = hash_password(user_password_in.new_password)
    session.add(user)
    await session.commit()
    return user


async def moderator_create():
    async with db_helper.session_factory() as session:
        stmt = select(User).filter(User.login == os.getenv("ADMIN_LOGIN"))
        moder = await session.execute(stmt)
        if not moder.scalar_one_or_none():
            new_moder = User(
                full_name="moderator",
                login=os.getenv("ADMIN_LOGIN"),
                email="admin@example.com",
                password=hash_password(os.getenv("ADMIN_PASSWORD")),
                role=UserRole.moder,
            )
            session.add(new_moder)
            await session.commit()
            return new_moder
        return "admin is already created"
