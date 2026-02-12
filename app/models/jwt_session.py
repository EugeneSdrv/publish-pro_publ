import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UUID, String, text
from sqlalchemy.orm import mapped_column, Mapped

from .db import Base


class JWTSession(Base):
    __tablename__ = "jwt_session"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    token_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    token: Mapped[str] = mapped_column(String, nullable=False)
    expires_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
