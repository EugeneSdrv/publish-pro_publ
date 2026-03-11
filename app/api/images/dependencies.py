from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
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
    try:
        entity_image = result.scalars().one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="image was not found"
        )
    return entity_image.post
