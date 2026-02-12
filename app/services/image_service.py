from fastapi import UploadFile
from sqlalchemy import select, delete

from app.api.images.crud import save_image
from app.conf.s3_client import s3client
from app.models import db_helper, PostImage, AvatarImage
from app.services.s3_services import S3ImageManager

# TODO: нужен рефактор
async def delete_images_without_post():
    async with db_helper.session_factory() as session:
        stmt = select(PostImage.image_key).where(PostImage.post_id == None)
        result = await session.execute(stmt)
        non_post_images_keys = result.scalars().all()
        stmt = select(AvatarImage.image_key).where(AvatarImage.user_id == None)
        result = await session.execute(stmt)
        non_user_images_keys = result.scalars().all()
        if non_post_images_keys:
            storage = S3ImageManager(
                bucket_name="post-illustration-images",
                client=await s3client.get_client(),
            )
            await storage.delete_objects(non_post_images_keys)
            stmt = delete(PostImage).where(PostImage.post_id == None)
            await session.execute(stmt)
            await session.commit()
        if non_user_images_keys:
            storage = S3ImageManager(
                bucket_name="users-avatar-images",
                client=await s3client.get_client(),
            )
            await storage.delete_objects(non_user_images_keys)
            stmt = delete(AvatarImage).where(AvatarImage.user_id == None)
            await session.execute(stmt)
            await session.commit()
            return f"Deleted {len(non_post_images_keys) + len(non_user_images_keys)} orphaned images"
        return "No orphaned images found"


async def create_image(
    file: UploadFile,
    session,
    storage,
    entity,
) -> PostImage:
    image_key = await storage.put_object(file)
    image = await save_image(image_key, session, entity)
    # TODO: надо понять как указать, что image будет иметь дополнительное поле image_url, кт-ое не хранится в таблице, но нужно для формирования ответа
    image.image_url = await storage.generate_url(image_key)
    await session.commit()
    return image
