from fastapi import APIRouter, status, Depends, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.users.dependencies import get_user_by_access
from app.api.users.schemas import UserUpdatePartial, UserUpdatePassword, UserSchema
from app.conf.s3_client import S3AsyncClient, s3client
from app.models import User, db_helper
from app.services import S3ImageManager, user_update, user_password_update

router = APIRouter(prefix="/users", tags=["Users"])
required_auth = HTTPBearer(auto_error=True)

@router.patch(
    "/update_user",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_in: UserUpdatePartial = Form(UserUpdatePartial, media_type="multipart/form-data"),
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
    user: User = Depends(get_user_by_access),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    client: S3AsyncClient = Depends(s3client.get_client),
):
    updated_user = await user_update(user_in, user, session, client)
    if getattr(updated_user, "image", None):
        updated_user.profile_image = updated_user.image.image_url
    elif user.profile_image:
        storage = S3ImageManager("users-avatar-images", client)
        updated_user.profile_image = await storage.generate_url(user.profile_image)
    return updated_user


@router.patch(
    path="/update_user_password",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user_password(
    user_password_in: UserUpdatePassword = Form(UserUpdatePassword, media_type="multipart/form-data"),
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
    user: User = Depends(get_user_by_access),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    client: S3AsyncClient = Depends(s3client.get_client),
):
    await user_password_update(user_password_in, user, session)
    if user.profile_image:
        storage = S3ImageManager("users-avatar-images", client)
        user.profile_image = await storage.generate_url(user.profile_image)
    return user
