import jwt
from fastapi import Depends, HTTPException, APIRouter, Form, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import crud as auth_crud
from app.api.users.dependencies import get_user_by_access
from app.api.users.schemas import TokenInfo, UserSchema, UserCreate
from app.api.auth import utils_jwt
from app.api.auth.dependencies import get_user_by_token, validate_auth_user
from app.conf.s3_client import S3AsyncClient, s3client
from app.models import db_helper, User
from app.services import S3ImageManager, user_service

router = APIRouter(prefix="/auth", tags=["Auth"])
required_auth = HTTPBearer(auto_error=True)

@router.get(
    "/my_profile", response_model=UserSchema, status_code=status.HTTP_200_OK
)
async def get_my_profile(
    creds: HTTPAuthorizationCredentials = Depends(required_auth),
    user: User = Depends(get_user_by_access),
    client: S3AsyncClient = Depends(s3client.get_client),
):
    if user.profile_image:
        storage = S3ImageManager("users-avatar-images", client)
        user.profile_image = await storage.generate_url(user.profile_image)
    return user


@router.post(
    "/registration", response_model=UserSchema, status_code=status.HTTP_201_CREATED
)
async def register_author(
    user_in: UserCreate = Form(UserCreate, media_type="multipart/form-data"),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
    client: S3AsyncClient = Depends(s3client.get_client),
):
    try:
        new_author = await user_service.create_user(
            user_in=user_in,
            session=session,
            client=client,
        )
        if user_in.profile_image:
            new_author.profile_image = new_author.image.image_url
        return new_author
    # TODO: нужно ли это здесь, если и да, то ролбекать нужно и созданное изображение
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error when creating a user",
        )
    finally:
        await session.close()


@router.post("/login", response_model=TokenInfo, status_code=status.HTTP_200_OK)
async def login_user(
    response: Response,
    user: UserSchema = Depends(validate_auth_user),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    access_token = utils_jwt.create_access_token(user)
    refresh_token = utils_jwt.create_refresh_token(user)
    try:
        await auth_crud.create_jwt_session(user, refresh_token, session)
    except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorised",
        )
    finally:
        await session.close()
    utils_jwt.set_refresh_to_cookie(refresh_token, response)
    return TokenInfo(access_token=access_token)


@router.post("/refresh", response_model=TokenInfo, status_code=status.HTTP_200_OK)
async def refresh_jwt_session(
    request: Request,
    response: Response,
    user: UserSchema = Depends(get_user_by_token),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    access_token = utils_jwt.create_access_token(user)
    refresh_token = utils_jwt.create_refresh_token(user)
    try:
        await auth_crud.update_jwt_session(refresh_token, request, session)
    except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorised",
        )
    finally:
        await session.close()
    utils_jwt.delete_refresh_from_cookie(response)
    utils_jwt.set_refresh_to_cookie(refresh_token, response)
    return TokenInfo(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    try:
        await auth_crud.delete_jwt_session(session, request)
    except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorised",
        )
    finally:
        await session.close()
    utils_jwt.delete_refresh_from_cookie(response)
    return {"logout": "success"}
