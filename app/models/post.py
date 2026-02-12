import uuid
from enum import StrEnum
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Enum, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from . import Base


class PublishStatus(StrEnum):
    draft = "draft"
    # не опубликовано как новое, при создании (возможна промежуточная версия в бд)
    pending_review = "pending_review"
    # при публикации статья отправляется на проверку модераторами
    published = "published"  # опубликовано
    unpublished = "unpublished"
    # на внесении изменений(временно не отображается в выдаче)
    archived = "archived"
    # удалено\архивировано, метод delete не должен удалять запись из бд


class Tag(Base):
    __tablename__ = "tags"

    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    title: Mapped[str]
    marked_posts: Mapped[list["Post"]] = relationship(
        back_populates="pinned_tags",
        secondary="posts_tags",
    )


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text, default="", server_default="")
    post_image: Mapped[Optional[str]]
    # series_posts_name: Mapped[Optional[str]] на данный момент реализация вне планов
    author_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    # необходимо определить параметр 'on_delete',
    # возможно стоит сохранять имя автора без ссылки на него, а не Set Null
    pinned_tags: Mapped[Optional[list["Tag"]]] = relationship(
        back_populates="marked_posts",
        secondary="posts_tags",
    )
    publish_status: Mapped[PublishStatus] = mapped_column(
        Enum(PublishStatus), default=PublishStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())")
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=text("TIMEZONE('utc', now())"),
    )
    images: Mapped[list["PostImage"]] = relationship(back_populates="post")


class PostTag(Base):
    __tablename__ = "posts_tags"

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.post_id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.tag_id"), primary_key=True)


class PostImage(Base):
    __tablename__ = "post_images"

    image_key: Mapped[str] = mapped_column(primary_key=True)
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "posts.post_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    post: Mapped["Post"] = relationship(back_populates="images")
