import os
import jwt

from fastapi import (Depends, HTTPException, Request)
from sqlalchemy.ext.asyncio import (AsyncSession)

from app.crud import (get_user)
from app.database import (get_db)
from app.logging_config import log
from app.schemas import (User)
from app.utils import (load_keys, SPECIAL_TOKEN)

ALGORITHM = os.getenv("ALGORITHM")


async def get_current_user(request: Request,
                           db: AsyncSession = Depends(get_db)) -> User:
    """
    Retrieves the current user from the request.

    Args:
        request (Request): The HTTP request object.
        db (AsyncSession, optional): The database session. Defaults to the session from `get_db`.

    Raises:
        HTTPException: If the user is not found, or is not active or blocked.

    Returns:
        User: The current user.

    """
    from app.utils import PUBLIC_KEY
    if PUBLIC_KEY is None:
        await load_keys()

    token = request.cookies.get("access_token")
    if not token:
        log.bind(type="users",
                 method=request.method,
                 current_user_id=-1,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).info(f"Guest visiting the site")
        raise HTTPException(status_code=401, detail="Please login")
    user = None
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        special_token = payload.get("special_token")
        if user_id is None or special_token != SPECIAL_TOKEN:
            log.bind(type="users",
                     method=request.method,
                     current_user_id=-2,
                     url=str(request.url),
                     headers=dict(request.headers),
                     params=dict(request.query_params)
                     ).error(f"Someone try to do fake token")
            raise HTTPException(status_code=401, detail="Unauthorized")
        user = await get_user(request=request, user_id=user_id, db=db)
    except jwt.PyJWTError:
        log.bind(type="users",
                 method=request.method,
                 current_user_id=user.id if user else -2,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).info(f"User's session ended")
        raise HTTPException(status_code=401, detail="Unauthorized")

    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not user.is_active or user.block_date is not None:
        log.bind(type="users",
                 method=request.method,
                 current_user_id=user.id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Permission denied")
        raise HTTPException(status_code=403, detail="Permission Denied")

    elif not user.is_verified:
        log.bind(type="users",
                 method=request.method,
                 current_user_id=user.id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Permission denied")
        raise HTTPException(status_code=402, detail="Permission Denied")

    return user


async def get_admin_user(request: Request,
                         current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current user if they are an admin.

    Args:
        request (Request): The HTTP request object.
        current_user (User, optional): The current user. Defaults to the user from `get_current_user`.

    Returns:
        User: The current user if they are an admin.

    Raises:
        HTTPException: If the user is not an admin.

    Logs:
        - Logs an error message if the user is not an admin.
    """
    if not current_user.is_superuser:
        if current_user.role != "admin":
            log.bind(type="admins",
                     method=request.method,
                     current_user_id=current_user.id,
                     url=str(request.url),
                     headers=dict(request.headers),
                     params=dict(request.query_params)
                     ).error(f"Permission denied")
            raise HTTPException(status_code=403, detail="Permission denied")

    return current_user


async def get_superadmin_user(request: Request,
                              current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current user if they are a superadmin.

    Args:
        request (Request): The HTTP request object.
        current_user (User, optional): The current user. Defaults to the user from `get_current_user`.

    Returns:
        User: The current user if they are a superadmin.

    Raises:
        HTTPException: If the user is not a superadmin.

    Logs:
        - Logs an error message if the user is not a superadmin.
    """
    if not current_user.is_superuser:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=current_user.id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Permission denied")
        raise HTTPException(status_code=403, detail="Permission denied")
    return current_user


async def check_user(request: Request,
                     user_id: int,
                     current_user: User,
                     db: AsyncSession) -> User:
    """
    Check if the user with the given `user_id` exists and if the current user has permission to access it.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to check.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        User: The user object if the user exists and the current user has permission to access it.

    Raises:
        HTTPException: If the user does not exist or the current user does not have permission to access it.
    """
    user = await get_user(request=request, user_id=user_id,
                          current_user=current_user, db=db)
    if user is None:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=current_user.id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"User not found")
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def check_user_for_superuser(request: Request,
                                   user_id: int,
                                   current_user: User,
                                   db: AsyncSession) -> User:
    """
    Check if the user with given `user_id` is a superuser and if the current user is not a superuser.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to check.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        User: The user object if the user is a superuser and the current user is not a superuser.

    Raises:
        HTTPException: If the user is a superuser and the current user is not a superuser.

    Logs:
        - Logs an error message if the user is a superuser and the current user is not a superuser.
    """
    user = await check_user(request, user_id, current_user, db)

    if user.is_superuser and not current_user.is_superuser:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=current_user.id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params)
                 ).error(f"Permission denied")
        raise HTTPException(status_code=403, detail="Permission denied")

    return user
