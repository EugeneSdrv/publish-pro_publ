import uuid
from enum import StrEnum

from sqlalchemy import String, Enum, UUID, text, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from . import Base


class UserRole(StrEnum):
    author = "author"
    moder = "moderator"
    admin = "administrator"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    profile_image: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    login: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.author)
    images: Mapped[list["AvatarImage"]] = relationship(back_populates="user")


class AvatarImage(Base):
    __tablename__ = "user_images"

    image_key: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    user: Mapped["User"] = relationship(back_populates="images")
