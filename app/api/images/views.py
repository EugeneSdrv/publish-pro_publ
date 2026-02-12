import uuid

from fastapi import UploadFile, File, APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.images.dependencies import get_post_by_image_key
from app.api.posts.dependencies import post_by_id
from app.api.images import permitions as perm
from app.api.images import crud
from app.conf.s3_client import s3client, S3AsyncClient
from app.models import Post,  db_helper
from app.services import image_service, S3ImageManager

router = APIRouter(tags=["Post images"])


class ImageResponse(BaseModel):
    image_key: str
    post_id: uuid.UUID
    image_url: str | None = None


@router.post(
    "/post/{post_id}/upload_image",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    post_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    file: UploadFile = File(...),
    post: Post = Depends(post_by_id),
    client: S3AsyncClient = Depends(s3client.get_client)
):
    if not post:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post by id {post_id} not found",
        )
    if perm.authorise_post_image_management(post, request):
        s3storage = S3ImageManager("post-illustration-images", client)
        return  await image_service.create_image(
            file,
            session,
            entity=post,
            storage=s3storage,
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )


@router.delete(
    "/post/delete_image/{image_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_image(
    request: Request,
    image_key: str,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    post: Post = Depends(get_post_by_image_key),
    client: S3AsyncClient = Depends(s3client.get_client)
):
    if perm.authorise_post_image_management(post, request):
        storage = S3ImageManager("post-illustration-images", client)
        await storage.delete_object(image_key)
        await crud.delete_image(image_key, session, post)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized",
    )


@router.get(
    "/post/get_images/{post_id}",
    response_model=list[ImageResponse],
    status_code=status.HTTP_200_OK,
)
async def get_post_images(
    request: Request,
    post_id: uuid.UUID,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    post: Post = Depends(post_by_id),
):
    if perm.authorise_post_image_management(post, request):
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post by id {post_id} not found",
            )
    return await crud.get_post_images(post, session)
