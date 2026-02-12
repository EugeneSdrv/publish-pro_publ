from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PostImage, Post, AvatarImage, User


async def save_image(
    image_key,
    session: AsyncSession,
    entity,
):
    if isinstance(entity, Post):
        image = PostImage(image_key=image_key, post_id=entity.post_id)
    elif isinstance(entity, User):
        image = AvatarImage(image_key=image_key, user_id=entity.user_id)
    else:
        raise TypeError(f"Expected User or Post, got {type(entity).__name__}")
    session.add(image)
    return image


async def delete_image(
    # TODO вытащить отсюда логику взаимодействия с s3 хранилищем
    image_key: str,
    session: AsyncSession,
    entity,
    ):
    if type(entity) == User:
        table = AvatarImage
    elif type(entity) == Post:
        table = PostImage
    else:
        raise TypeError(f"Expected User or Post, got {type(entity).__name__}")
    image = await session.get(table, image_key)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"image by key {image_key} not found",
        )
    await session.delete(image)
    await session.commit()
    return image_key


async def get_post_images(
    post: Post,
    session: AsyncSession,
):
    statement = select(PostImage).filter(PostImage.post_id == post.post_id)
    result = await session.execute(statement)
    images = result.scalars().all()
    return list(images)
