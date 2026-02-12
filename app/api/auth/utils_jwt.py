import os
import uuid
from datetime import datetime, timedelta, UTC

from argon2 import PasswordHasher
import jwt
from dotenv import load_dotenv


load_dotenv()


def encode_jwt(
    token_type,
    payload,
):
    token_type_header = {"type": token_type}
    encoded = jwt.encode(
        headers=token_type_header,
        payload=payload,
        key=os.getenv("SECRET_KEY"),
        algorithm="HS256",
    )
    return encoded


def decode_jwt(
    token: str,
    options: dict = None,
):
    decoded = jwt.decode(
        token,
        key=os.getenv("SECRET_KEY"),
        algorithms="HS256",
        options=options,
    )
    return decoded


def create_access_token(user):
    payload = {
        "sub": str(user.user_id),
        "role": user.role,
        "exp": datetime.now(UTC) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE"))),
    }
    return encode_jwt("access", payload)


def create_refresh_token(user):
    payload = {
        "sub": str(user.user_id),
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE"))),
    }
    return encode_jwt("refresh", payload)


def set_refresh_to_cookie(
    refresh,
    response,
):
    return response.set_cookie(
        "refresh_token",
        refresh,
        path="/api/v1/auth",
        httponly=True,
    )


def delete_refresh_from_cookie(response):
    return response.delete_cookie(
        "refresh_token",
        path="/api/v1/auth",
        httponly=True,
    )


ph = PasswordHasher()


def hash_password(
    password: str,
):
    return ph.hash(password)


def validate_password(
    password,
    hashed_password,
):
    return ph.verify(
        hashed_password,
        password,
    )
