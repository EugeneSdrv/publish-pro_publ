from fastapi import Request, HTTPException, status

from app.models import PublishStatus, Post


def authorise_post_content_image_management(
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


def authorise_post_content_image_delete(
    image_key,
    post: Post,
    request: Request,
) -> bool:
    """
    Если пользователь является автором публикации и публикация в статусах 'draft' или
    'unpublished', то изображения можно удалять.
    :image_key: Ключ изображение, которое нужно удалить.
    :param post: Публикация.
    :param request: Запрос, в котором содержится id пользователя.
    :return:
    """
    if request.state.user_id == post.author_id:
        if post.publish_status in (PublishStatus.draft, PublishStatus.unpublished) and post.post_image != image_key:
            return True
        elif post.publish_status in (PublishStatus.draft, PublishStatus.unpublished) and post.post_image == image_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="to delete an image post, use the api/posts/delete_post_image/{post_id} handler",
            )
    return False
