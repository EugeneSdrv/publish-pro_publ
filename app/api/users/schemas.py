import uuid
from typing import Annotated

from fastapi import File, UploadFile
from pydantic import EmailStr, BaseModel, ConfigDict, Field

from app.models import UserRole


class UserBase(BaseModel):
    full_name: str
    login: str
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="A password must contain at least one uppercase letter, one lowercase letter,\
        one digit, and one special character and must be between 8 and 32 characters long",
    )


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    full_name: str
    login: str
    email: EmailStr
    profile_image: str | None
    role: UserRole


class UserCreate(UserBase):
    profile_image: Annotated[UploadFile, File()] | str = None


class TokenInfo(BaseModel):
    access_token: str


class UserUpdatePartial(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    profile_image: Annotated[UploadFile, File()] | str = None
    password: str = Field(
        ...,
        min_length=8,
        max_length=32,
    )


class UserUpdatePassword(BaseModel):
    current_password: str = Field(
        ...,
        min_length=8,
        max_length=32,
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=32,
        description="A password must contain at least one uppercase letter, one lowercase letter,\
        one digit, and one special character and must be between 8 and 32 characters long",
    )
