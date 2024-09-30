import datetime
import os
from typing import (List, Sequence, Any)

import httpx
from passlib.context import (CryptContext)

from fastapi.exceptions import (HTTPException)
from fastapi import (Request)

from sqlalchemy import (Row, RowMapping)
from sqlalchemy.ext.asyncio import (AsyncSession)
from sqlalchemy.future import (select)

from app.database import redis_client
from app.models import (User)
from app.schemas import (UserCreate)
from app.logging_config import (log)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TELEGRAM_BOT_URL = os.getenv("TELEGRAM_BOT_URL")

async def get_user(request: Request,
                   user_id: int,
                   db: AsyncSession,
                   current_user: User = None) -> Row[Any] | RowMapping | None:
    """
        Asynchronously gets a user by their ID from the database.

        Args:
            request (Request): The HTTP request object.
            user_id (int): The ID of the user to retrieve.
            db (AsyncSession): The database session.
            current_user (User, optional): The current user. Defaults to None.

        Returns:
            Row[Any] | RowMapping | None: The user object if found, None if not found and the current user is None, otherwise raises HTTPException.

        Raises:
            HTTPException: If the user is not found and the current user is not None.
    """
    if current_user is None:
        current_user_id = -3
    else:
        current_user_id = current_user.id
    query = await db.execute(select(User).filter(User.id == user_id))
    result = query.scalars().first()
    if result is None:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=current_user_id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Try to take info about user: {user_id}. But user not found")
        if current_user is None:
            return None
        raise HTTPException(400, detail="User not found")
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user_id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info about user: {user_id}")
    return result


async def check_email(request: Request,
                      email: str,
                      db: AsyncSession) -> bool:
    """
    Check if an email exists in the database.

    Args:
        request (Request): The HTTP request object.
        email (str): The email to check.
        db (AsyncSession): The database session.

    Returns:
        bool: True if the email is not found, False if the email is found.

    Raises:
        None

    Logs:
        - If the email is not found in the database, logs an error message.
        - If the email is found in the database, logs an info message.
    """
    query = await db.execute(select(User).filter(User.email == email))
    result = query.scalars().first()
    if result is None:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=-3,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Email {email} not found in database")
        return True
    log.bind(type="admins",
             method=request.method,
             current_user_id=-3,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Email {email} was found in database")
    return False


async def get_user_by_email(request: Request,
                            email: str,
                            db: AsyncSession,
                            current_user: User = None) -> Row[Any] | RowMapping | User | None:
    """
    Get a user by their email.

    Args:
        request (Request): The HTTP request object.
        email (str): The email of the user to retrieve.
        db (AsyncSession): The database session.
        current_user (User, optional): The current user. Defaults to None.

    Returns:
        User: The user object if found, None if not found and the current user is None, otherwise raises HTTPException.

    Raises:
        HTTPException: If the user is not found and the current user is not None.
    """
    if current_user is None:
        current_user_id = -3
    else:
        current_user_id = current_user.id
    query = await db.execute(select(User).filter(User.email == email))
    result = query.scalars().first()
    if result is None:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=current_user_id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Try to take info about user: {email}. But user not found")
        if current_user is None:
            return None
        raise HTTPException(400, detail="User not found")
    log.bind(type="admins",
             method=request.method,
             current_user_id=-current_user_id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info about user: {email}")
    return result


async def get_all_users(request: Request,
                        current_user: User,
                        db: AsyncSession) -> Sequence[User]:
    """
    Get all users from the database.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        List[User]: A list of all users in the database.

    Raises:
        None

    Logs:
        - Logs an info message indicating that info about all users has been gained.
    """
    result = await db.execute(select(User))
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info about all users")
    return result.scalars().all()


async def get_unblocked_users(request: Request,
                              current_user: User,
                              db: AsyncSession) -> Sequence[User]:
    """
    Get all users from the database where `is_active` is True.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        List[User]: A list of all users in the database where `is_active` is True.

    Raises:
        None

    Logs:
        - Logs an info message indicating that info about unblocked users has been gained.
    """
    result = await db.execute(select(User).where(User.is_active is True))
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info about unblocked users")
    return result.scalars().all()


async def get_blocked_users(request: Request,
                            current_user: User,
                            db: AsyncSession) -> Sequence[User]:
    """
    Get all users from the database where `is_active` is False.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        List[User]: A list of all users in the database where `is_active` is False.

    Raises:
        None

    Logs:
        - Logs an info message indicating that info about blocked users has been gained.
    """
    result = await db.execute(select(User).where(User.is_active is False))
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info about blocked users")
    return result.scalars().all()


async def get_users(request: Request,
                    current_user: User,
                    db: AsyncSession,
                    skip: int = 0,
                    limit: int = 10) -> Sequence[User]:
    """
    Get users from the database.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        db (AsyncSession): The database session.
        skip (int): The number of records to skip. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 10.

    Returns:
        List[User]: A list of users from the database.

    Raises:
        None

    Logs:
        - Logs an info message indicating that info from a range of users has been gained.
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info from {skip} to {skip + limit} users")
    return result.scalars().all()


async def create_user(request: Request,
                      user: UserCreate,
                      db: AsyncSession,
                      current_user: User = None) -> User:
    """
    Create a new user in the database.

    Args:
        request (Request): The HTTP request object.
        user (UserCreate): The user data to create.
        db (AsyncSession): The database session.
        current_user (User, optional): The current user. Defaults to None.

    Returns:
        User: The newly created user.

    Raises:
        None

    Logs:
        - Logs an info message indicating the creation of a new user.

    """
    hashed_password = pwd_context.hash(user.password)
    if user.email == "stepanov.iop@gmail.com":
        db_user = User(
            email=user.email.strip(),
            hashed_password=hashed_password,
            first_name=user.first_name.strip().lower(),
            last_name=user.last_name.strip().lower(),
            middle_name=user.middle_name.strip().lower(),
            phone_number=user.phone_number,
            role="superadmin",
            is_verified=True,
            is_superuser=True
        )
    else:
        db_user = User(
            email=user.email.strip(),
            hashed_password=hashed_password,
            first_name=user.first_name.strip().lower(),
            last_name=user.last_name.strip().lower(),
            middle_name=user.middle_name.strip().lower(),
            phone_number=user.phone_number
        )
    db.add(db_user)
    await db.flush()  # Flush to ensure that db_user gets an ID
    await db.refresh(db_user)  # Refresh the instance to make sure we have all data, including generated fields
    await db.commit()  # Commit the transaction

    log.bind(type="admins",
             method=request.method,
             current_user_id=-3,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Created user {db_user.id}")
    return db_user


async def get_unverified_users(request: Request,
                               current_user: User,
                               db: AsyncSession) -> Sequence[User]:
    """
    Get all users from the database where `is_verified` is False.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        List[User]: A list of all users in the database where `is_verified` is False.

    Raises:
        None

    Logs:
        - Logs an info message indicating that info about unverified users has been gained.

    """
    result = await db.execute(select(User).where(User.is_verified == False))
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained info about unverified users")
    return result.scalars().all()


async def hash_func(word: str) -> str:
    """
    Hash a given string using the configured password context.

    Args:
        word (str): The string to be hashed.

    Returns:
        str: The hashed string.
    """
    return pwd_context.hash(word)


async def update_user_role(request: Request,
                           current_user: User,
                           user: User,
                           role: str,
                           db: AsyncSession) -> User:
    """
    Update the role of a user in the database.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        user (User): The user whose role is to be updated.
        role (str): The new role to be set for the user.
        db (AsyncSession): The database session.

    Returns:
        User: The updated user object.

    Raises:
        None

    Logs:
        - Logs an info message indicating the updated user role.

    """
    user.role = role
    await db.commit()
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Updated user role: {user.id}")
    return user


async def update_user_status(request: Request,
                             current_user: User,
                             user: User,
                             is_verified: bool,
                             db: AsyncSession) -> User:
    """
    Update the verification status of a user in the database.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        user (User): The user whose verification status is to be updated.
        is_verified (bool): The new verification status to be set for the user.
        db (AsyncSession): The database session.

    Returns:
        User: The updated user object.

    Raises:
        None

    Logs:
        - Logs an info message indicating the updated user verification status.

    """
    user.is_verified = is_verified
    await db.commit()
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Verified user: {user.id}")
    return user


async def block_user(request: Request,
                     current_user: User,
                     user: User,
                     db: AsyncSession) -> User:
    """
    Block user

    Blocks a user by setting their `is_active` field to `False`
    and setting their `block_date` field to the current UTC time.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        user (User): The user to be blocked.
        db (AsyncSession): The database session.

    Returns:
        User: The blocked user.

    Logs:
        - Logs an info message indicating the ID of the blocked user.
    """
    user.is_active = False
    user.block_date = datetime.datetime.utcnow()
    await db.commit()
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Blocked user: {user.id}")
    return user


async def unblock_user(request: Request,
                       current_user: User,
                       user: User,
                       db: AsyncSession) -> User:
    """
    Unblocks a user by setting their `is_active` field to `True` and setting their `block_date` field to `None`.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        user (User): The user to be unblocked.
        db (AsyncSession): The database session.

    Returns:
        User: The unblocked user.

    Logs:
        - Logs an info message indicating the ID of the unblocked user.
    """
    user.is_active = True
    user.block_date = None
    await db.commit()
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Unblocked user: {user.id}")
    return user


def user_to_dict(user: User) -> dict:
    """
    Convert a User object to a dictionary representation.

    Args:
        user (User): The User object to be converted.

    Returns:
        dict: A dictionary containing the following keys and their corresponding values:
            - id (int): The ID of the user.
            - email (str): The email of the user.
            - first_name (str): The first name of the user.
            - last_name (str): The last name of the user.
            - middle_name (str): The middle name of the user.
            - phone_number (str): The phone number of the user.
            - role (str): The role of the user.
            - is_active (bool): Whether the user is active.
            - is_superuser (bool): Whether the user is a superuser.
            - is_verified (bool): Whether the user is verified.
            - registration_date (Optional[str]): The date of user registration, in ISO format.
            - block_date (Optional[str]): The date the user was blocked, in ISO format.
    """
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "middle_name": user.middle_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "registration_date": user.registration_date.isoformat() if user.registration_date else None,
        "block_date": user.block_date.isoformat() if user.block_date else None
    }


async def update_user(request: Request,
                      current_user: User,
                      user: User,
                      user_data: dict,
                      db: AsyncSession) -> User:
    """
    Update a user in the database.

    Args:
        request (Request): The HTTP request object.
        current_user (User): The current user.
        user (User): The user to be updated.
        user_data (dict): The updated user data.
        db (AsyncSession): The database session.

    Returns:
        User: The updated user object.

    Logs:
        - Logs an info message indicating the ID of the updated user.
    """
    old_data = user_to_dict(user)
    for key, value in user_data.items():
        setattr(user, key, value)
    db.add(user)
    await db.commit()
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             old_user_info=old_data,
             new_user_info=user_to_dict(user),
             params=dict(request.query_params)
             ).info(f"Updated user: {user.id}")
    return user

async def send_notification(phone_number: str, message: str) -> None:

    data = {
        'phone_number': phone_number,
        'message': message
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(TELEGRAM_BOT_URL, data=data)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to send notification to Telegram.")

async def send_notifications(notifications: dict) -> None:
    for phone_number, message in notifications.items():
        await send_notification(phone_number, message)

async def send_notification_to_all_users(phone_numbers: list, message: str) -> None:
    for user_number in phone_numbers:
        await send_notification(user_number, message)