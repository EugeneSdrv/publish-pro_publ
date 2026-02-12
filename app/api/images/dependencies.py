from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import PostImage, Post, db_helper


async def get_post_by_image_key(
    image_key,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> Post:
    statement = (
        select(PostImage)
        .where(PostImage.image_key == image_key)
        .options(selectinload(PostImage.post))
    )
    result = await session.execute(statement)
    return result.scalars().one().post
