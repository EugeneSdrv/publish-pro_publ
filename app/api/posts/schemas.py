import uuid
from typing import Annotated

from fastapi import UploadFile, File
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models import PublishStatus


class Tag(BaseModel):
    tag_id: int
    title: str


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    post_image: Annotated[UploadFile, File()] | str = None


class PostUpdate(PostBase): ...


class PostUpdatePartial(BaseModel):
    title: str | None = None
    content: str | None = None
    post_image: Annotated[UploadFile, File()] | str = None
    publish_status: PublishStatus | None = None


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    post_id: uuid.UUID
    author_id: uuid.UUID
    publish_status: str | None
    post_image: str
    created_at: datetime
    updated_at: datetime
