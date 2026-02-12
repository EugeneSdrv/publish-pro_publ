from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status, Request, HTTPException, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PublishStatus, db_helper
from app.conf.s3_client import S3AsyncClient, s3client
from app.services import post_service, S3ImageManager
from . import crud
from . import permitions as perm
from .schemas import PostResponse, PostUpdatePartial, PostCreate
from .dependencies import post_by_id

router = APIRouter(prefix="/posts", tags=["Posts"])
required_auth = HTTPBearer(auto_error=False)


@router.get(
    "/get_post/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
)
async def get_post(
    post_id: UUID,
    request: Request,
    post: Post = Depends(post_by_id),
):
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post by id {post_id} not found",
        )
    if perm.authorize_get_post(request=request, post=post):
        return post
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )


@router.get(
    "/get_posts",
    response_model=List[PostResponse],
    status_code=status.HTTP_200_OK,
)
async def get_posts(
    request: Request,
    publish_status: PublishStatus = PublishStatus.published,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Метод возвращает публикации, с фильтрацией по статусу. В зависимости от параметров проходит проверка прав доступа
    :return: list[Post]
    """
    if perm.authorize_get_posts(publish_status, request=request):
        result = await crud.get_filtered_posts(session, publish_status, request)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No publications such {publish_status} were found",
            )
        return result
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )


@router.post(
    "/create_post",
    response_model=None,  # PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    request: Request,
    post_in: PostCreate = Form(PostCreate, media_type="multipart/form-data"),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
    client: S3AsyncClient = Depends(s3client.get_client),
):
    if perm.authorize_create_post(request=request):
        return await post_service.create_post(post_in=post_in, session=session, request=request, client=client, )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )


@router.patch(
    "/update_post/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK,
)
async def update_post(
    request: Request,
    post_update: PostUpdatePartial,
    post: Post = Depends(post_by_id),
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    client: S3AsyncClient = Depends(s3client.get_client),
):
    if perm.authorize_post_changes(post_update=post_update, post=post, request=request):
        updated_post = await post_service.update_post(
            post=post,
            post_update=post_update,
            session=session,
            client=client,
            partial=True,
        )
        if getattr(updated_post, "image", None):
            updated_post.post_image = post.image.image_url
        elif updated_post.post_image:
            storage = S3ImageManager("post-illustration-images", client)
            post.post_image = await storage.generate_url(updated_post.post_image)
        return updated_post
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )


@router.delete("/delete_post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    request: Request,
    post: Post = Depends(post_by_id),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
):
    if perm.authorise_delete_post(request=request, post=post):
        return await crud.delete_post(post=post, session=session)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )
