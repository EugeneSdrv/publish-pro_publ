import uuid

from fastapi import HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PublishStatus


async def get_post(
    post_id: uuid.UUID,
    session: AsyncSession,
    request: Request,
) -> Post:
    post = await session.get(Post, post_id)
    if post:
        return post
    await session.close()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Post {post_id} not found!",
    )


async def get_filtered_posts(
    session: AsyncSession,
    publish_status: str,
    request: Request,
) -> list[Post]:
    filtered_query = select(Post).filter(Post.publish_status == publish_status)
    if publish_status != "published":
        if request.state.user_role == "author":
            filtered_query = filtered_query.filter(
                Post.author_id == request.state.user_id,
            )
    result = await session.execute(filtered_query)
    posts = result.scalars().all()
    return list(posts)


async def delete_post(
    post: Post,
    session: AsyncSession,
) -> None:
    post.publish_status = PublishStatus.archived
    session.add(post)
    await session.commit()
    await session.close()
