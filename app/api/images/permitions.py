from fastapi import Request

from app.models import PublishStatus, Post


def authorise_post_image_management(
    post: Post,
    request: Request,
) -> bool:
    """
    Если пользователь является автором публикации и публикация в статусах 'draft' или
    'unpublished', то изображения можно удалять и добавлять
    :param post: публикация
    :param request: запрос, в котором содержится id пользователя
    :return:
    """
    if request.state.user_id == post.author_id:
        if post.publish_status in (PublishStatus.draft, PublishStatus.unpublished):
            return True
    return False
