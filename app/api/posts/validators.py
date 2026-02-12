import re
import uuid

from sqlalchemy import select, not_

from app.services import S3ImageManager
from app.models import PostImage, db_helper


async def cleanup_unused_images(post, post_update):
    async with db_helper.session_factory() as session:
        storage = S3ImageManager("post-illustration-images")
        pattern = r"!$$Image description$$$(https?://[^\s)]+)$"
        # регулярное выражение для извлечения ссылок изображений из контента поста
        content_image_links = re.findall(pattern, post_update.content)
        # получаем список ссылок сопоставляя их шаблону
        # необходимо быть уверенным, что содержание поста не нарушено иначе может быть ОШИБКА
        content_image_uuid_keys = []
        for link in content_image_links:
            try:
                image_uuid = uuid.UUID(link.split("/")[-1])
                content_image_uuid_keys.append(image_uuid)
            except (TypeError, ValueError):
                continue
        # создаем список UUID-ключей возможны неправильные ссылки, тогда пропускаем ссылку и не добавляем uuid
        stmt = select(PostImage.image_key).where(
            PostImage.post_id == post.post_id,
            not_(PostImage.image_key.in_(content_image_uuid_keys)),
        )
        # делаем выборку image_key из таблицы Image строк с ключами, которых нет в 'content_image_uuid_keys'
        result = await session.execute(stmt)
        # получаем список ключей изображений, которые соответствуют запросу,
        # т.е. не использованы в содержании, но записи есть в таблице Image и соответственно в хранилище
        unused_content_image_entries = result.scalars().all()
    if unused_content_image_entries:
        await storage.delete_objects(unused_content_image_entries)
        # удаляем из хранилища не использованные в содержании ключи
        result = await session.execute(select(PostImage).filter(
            PostImage.post_id == post.post_id,
            not_(PostImage.image_key.in_(content_image_uuid_keys))),
        )
        await result.delete(synchronize_session=False)
        # удаляем записи из таблицы
        await session.commit()
        return
