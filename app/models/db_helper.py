import os
from asyncio import current_task

from dotenv import load_dotenv
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)

load_dotenv()


class DatabaseHelper:
    def __init__(self, url: URL, echo: bool = False):
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def _get_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )
        return session

    async def scoped_session_dependency(self):
        session = self._get_scoped_session()
        yield session
        await session.close()


url_object = URL.create(
    "postgresql+asyncpg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT"),
)

db_helper = DatabaseHelper(url_object, echo=False)
