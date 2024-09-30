import json
import os

import aiofiles
import jwt
import datetime
from passlib.context import (CryptContext)
from datetime import (timedelta)

from fastapi import (Request)
import pywebpush
from app.logging_config import (log)
from app.schemas import (User)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH")

ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

PRIVATE_KEY = None
PUBLIC_KEY = None

SPECIAL_TOKEN = os.getenv("SPECIAL_TOKEN")


async def create_access_token(request: Request,
                              current_user: User,
                              data: dict,
                              expires_delta: timedelta = None) -> str:
    """
    Creates a new JWT access token with an expiration time either specified
    by the `expires_delta` parameter or the `ACCESS_TOKEN_EXPIRE_MINUTES`
    environment variable.

    Args:
        request (Request): The incoming HTTP request object.
        current_user (User): The user for whom the token is being created.
        data (dict): Additional data to include in the token.
        expires_delta (timedelta, optional): The time until the token expires.
            If not provided, the token will expire after `ACCESS_TOKEN_EXPIRE_MINUTES`.

    Returns:
        str: The encoded JWT access token.

    Raises:
        None

    Logs:
        - Logs an info message indicating the creation of a new token.
    """
    if PRIVATE_KEY is None:
        await load_keys()

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "special_token": SPECIAL_TOKEN})
    encoded_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)
    log.bind(type="users",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Token was created in {datetime.datetime.utcnow()}")
    return encoded_jwt


async def verify_password(plain_password,
                          hashed_password) -> bool:
    """
    Verify a plain text password against a hashed password.

    This function uses the `passlib` library to verify a plain text password
    against a hashed password. If the plain text password matches the hashed
    password, this function returns `True`. Otherwise, it returns `False`.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: `True` if the plain text password matches the hashed password,
            `False` otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def load_keys() -> None:
    """
    Asynchronously loads the private and public keys from the file system.

    This function opens the files specified by the `PRIVATE_KEY_PATH` and
    `PUBLIC_KEY_PATH` environment variables and reads their contents. The
    contents are then assigned to the `PRIVATE_KEY` and `PUBLIC_KEY` global
    variables.

    This function is typically used to load the keys from the file system when
    the application starts up, or when the keys need to be reloaded.

    Returns:
        None
    """
    global PRIVATE_KEY, PUBLIC_KEY
    async with aiofiles.open(PRIVATE_KEY_PATH, "r") as private_file:
        PRIVATE_KEY = await private_file.read()
    async with aiofiles.open(PUBLIC_KEY_PATH, "r") as public_file:
        PUBLIC_KEY = await public_file.read()

