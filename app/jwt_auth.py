import os
import jwt
from datetime import (datetime)

from fastapi import (HTTPException)

from app.database import redis_client

NOTIFICATION_SECRET_KEY = os.getenv("NOTIFICATION_SECRET_KEY")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def decode_terminal_token(token: str) -> dict:
    """
    Decode a terminal token and return its payload.

    Args:
        token (str): The token to decode.

    Returns:
        dict: The payload of the token.

    Raises:
        HTTPException: If the token is invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")


def create_terminal_token(terminal_id: int,
                          registration_date: datetime,
                          uid: str) -> str:
    """
    Create a terminal token.

    Args:
        terminal_id (int): The terminal ID.
        registration_date (datetime): The registration date.
        uid (str): The user ID.

    Returns:
        str: The generated token.
    """
    payload = {
        "terminal_id": terminal_id,
        "registration_date": registration_date.isoformat(),
        "uid": uid
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_terminal(token: str) -> dict:
    """
    Verify a terminal token and return its payload.

    Args:
        token (str): The token to verify.

    Returns:
        dict: The payload of the token.

    Raises:
        HTTPException: If the token is expired or invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Signature has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def generate_notification_token(application_user_id: str) -> str:
    to_encode = {"application_user_id": application_user_id, "notification_secret_key": NOTIFICATION_SECRET_KEY}
    encoded_jwt = jwt.encode(to_encode, ACCESS_TOKEN_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_notification_token(token: str, user_telegram_id: int) -> bool:
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET, algorithms=[ALGORITHM])
        application_user_id = payload.get("application_user_id")
        notification_secret_key = payload.get("notification_secret_key")
        if not application_user_id or not notification_secret_key or notification_secret_key != NOTIFICATION_SECRET_KEY:
            return False
        if redis_client is None:
            raise Exception("Redis client is not initialized. Call init_redis() first.")
        await redis_client.set(application_user_id, user_telegram_id)
        return True

    except jwt.PyJWTError:
        return False


