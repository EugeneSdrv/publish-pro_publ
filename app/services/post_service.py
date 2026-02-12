from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.images.crud import delete_image
from app.services.image_service import create_image
from app.api.posts.schemas import PostUpdate, PostUpdatePartial
from app.models import Post
from app.services.s3_services import S3ImageManager


async def create_post(
    post_in,
    session: AsyncSession,
    request: Request,
    client,
) -> Post:
    post = Post(**post_in.model_dump(exclude={"post_image"}))
    post.author_id = request.state.user_id
    session.add(post)
    await session.flush()
    if post_in.post_image:
        storage = S3ImageManager("post-illustration-images", client)
        image = await create_image(post_in.post_image, session, storage, post)
        post.post_image = image.image_key
        session.add(post)
        await session.commit()
        post.post_image = image.image_url
        return post
    session.add(post)
    await session.commit()
    return post


async def update_post(
    post: Post,
    post_update: PostUpdate | PostUpdatePartial,
    session: AsyncSession,
    client,
    partial: bool = False,
) -> Post:
    for field, value in post_update.model_dump(exclude_unset=partial).items():
        if field == "post_image" and value:
            storage = S3ImageManager("post-illustration-images", client)
            if image_key := post.post_image:
                await storage.delete_object(image_key)
                await delete_image(image_key, session, post)
            post.image = await create_image(post_update.post_image, session, storage, post)
            setattr(post, field, post.image.image_key)
        else:
            setattr(post, field, value)
    session.add(post)
    await session.commit()
    return post
