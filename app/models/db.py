import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import URL

import os

from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

url_object = URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT"),
)
engine = sqlalchemy.create_engine(url_object)
session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    __abstract__ = True
