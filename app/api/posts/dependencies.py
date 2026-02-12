import uuid
from typing import Annotated

from fastapi import Path, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.posts import crud
from app.models import Post, db_helper


async def post_by_id(
    post_id: Annotated[uuid.UUID, Path],
    request: Request,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> Post:
    return await crud.get_post(post_id=post_id, session=session, request=request)
