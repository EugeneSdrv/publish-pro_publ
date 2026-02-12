from app.models import PublishStatus, UserRole


def authorize_get_post(request, post):
    """
    Получать опубликованный пост могут даже неавторизованные пользователи.
    Для всех остальных нужна аутентификация.
    Получить пост в статусе "pending_review" могут только модераторы.  # нет
    Получить пост в статусах "draft", "unpublished" может только автор этого поста.  # нет
    :param request:
    :param post:
    :return:
    """
    if post.publish_status == PublishStatus.published:
        return True
    else:
        if post.author_id == request.state.user_id:
            return True
        if post.publish_status in (
            PublishStatus.pending_review,
            PublishStatus.published,
        ):
            if request.state.user_role == UserRole.moder:
                return True
    return False


def authorize_get_posts(publish_status, request):
    """
    Получать опубликованные посты могут даже неавторизованные пользователи.
    Для всех остальных нужна аутентификация.
    Получать посты в статусе "pending_review" могут только модераторы.
    Получать посты в статусах "draft", "unpublished" может только автор этих постов.
    !!! Получение постов в статусе "archived" не реализовано. И сценарий назначения постов в данный статус не определен.!!!
    :param publish_status:
    :param request:
    :return:
    """
    if publish_status == PublishStatus.published:
        return True
    else:
        if request.state.user_role == UserRole.author:
            return True
        if publish_status in (PublishStatus.pending_review, PublishStatus.published):
            if request.state.user_role == UserRole.moder:
                return True
    return False


# ----------------------------------------------------


def authorize_post_status_change(post_update, post, request):
    """
    Если статья находится в статусах "draft"(проект), "unpublished" только автор может установить статус "on_review".
    Если статья находится в статусе "pending_review" только модератор может установить статус "published" или откатить на
    предыдущий статус "draft", "unpublished".
    :param post_update:
    :param post:
    :param request:
    :return:
    """
    if post.author_id == request.state.user_id:
        if (
            post.publish_status in (PublishStatus.draft, PublishStatus.unpublished)
            and post_update.publish_status == PublishStatus.pending_review
        ):
            return True
        if (
            post.publish_status
            in (PublishStatus.published, PublishStatus.pending_review)
            and post_update.publish_status == PublishStatus.unpublished
        ):
            return True
        if (
            post.publish_status in PublishStatus.archived
            and post_update.publish_status == PublishStatus.unpublished
        ):
            return True

    elif request.state.user_role == UserRole.moder:
        if (
            post.publish_status == PublishStatus.pending_review
            and post_update.publish_status
            in (PublishStatus.published, PublishStatus.draft, PublishStatus.unpublished)
        ):
            return True
        if (
            post.publish_status == PublishStatus.published
            and post_update.publish_status == PublishStatus.unpublished
        ):
            return True
    return False


def authorize_title_change(post_update, post, request):
    """
    Если статья еще не была опубликована, т.е находится в статусе "draft"(проект) заголовок может менять только автор.
    :param post_update:
    :param post:
    :param request:
    :return:
    """
    if (
        post.publish_status in (PublishStatus.draft, PublishStatus.unpublished)
        and post.author_id == request.state.user_id
    ):
        return True
    return False


def authorize_content_change(post_update, post, request):
    """
    Если статья не опубликована, т.е находится в статусах "draft"(проект), "unpublished" содержание статьи может менять только автор.
    :param post_update:
    :param post:
    :param request:
    :return:
    """
    if (
        post.publish_status in (PublishStatus.draft, PublishStatus.unpublished)
        and post.author_id == request.state.user_id
    ):
        return True
    return False


def authorize_pinned_tags_change(post_update, post, request):
    """
    Если статья не опубликована, т.е находится в статусах "draft"(проект), "unpublished" прикрепленные теги может менять только автор.
    :param post_update:
    :param post:
    :param request:
    :return:
    """
    if (
        post.publish_status in (PublishStatus.draft, PublishStatus.unpublished)
        and post.author_id == request.state.user_id
    ):
        return True
    return False


def authorize_post_image_change(post_update, post, request):
    """
    Если статья не опубликована, т.е находится в статусах "draft"(проект), "unpublished" изображение может менять только автор.
    :param post_update:
    :param post:
    :param request:
    :return:
    """
    if (
        post.publish_status in (PublishStatus.draft, PublishStatus.unpublished)
        and post.author_id == request.state.user_id
    ):
        return True
    return False


# ----------------------------


def authorize_create_post(request) -> bool:
    """
    Если пользователь имеет роль "author", он может создавать статьи
    :param request:
    :return:
    """
    if request.state.user_role == UserRole.author:
        return True
    return False


def authorise_delete_post(request, post) -> bool:
    """
    Если пользовать это автор поста, он может удалить этот пост (т.е. перевести публикацию в статус "archive")
    :param request:
    :param post:
    :return:
    """
    if post.author_id == request.state.user_id:
        return True
    return False


def authorize_post_changes(post_update, post, request):
    authorizers = {
        "title": authorize_title_change,
        "content": authorize_content_change,
        "post_image": authorize_post_image_change,
        "pinned_tags": authorize_pinned_tags_change,
        "publish_status": authorize_post_status_change,
    }
    for field, authorizer in authorizers.items():
        if getattr(post_update, field, None):
            if not authorizer(post_update, post, request):
                return False
    return True
