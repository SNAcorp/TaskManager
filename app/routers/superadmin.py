from fastapi import (APIRouter, Depends, Request)

from sqlalchemy.ext.asyncio import (AsyncSession)

from app.database import (get_db)
from app.schemas import (User)
from app.crud import (update_user_role, update_user_status)
from app.dependencies import (get_superadmin_user, check_user, check_user_for_superuser)

router = APIRouter()


@router.put("/verify/{user_id}", response_model=User)
async def verify_user(request: Request,
                      user_id: int,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_superadmin_user)) -> User:
    """
    Verify a user by updating their status to active.

    Parameters:
        user_id (int): The ID of the user to verify.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        User: The updated user object.

    This function verifies a user by updating their status to active in the
    database. The user is identified by their ID and the current user is
    authenticated using the `get_superadmin_user` dependency. The function
    returns the updated user object.
    :param user_id:
    :param current_user:
    :param db:
    :param request:
    """
    user = await check_user(request=request,
                            user_id=user_id,
                            current_user=current_user,
                            db=db)
    updated_user = await update_user_status(request=request,
                                            user=user,
                                            current_user=current_user,
                                            is_verified=True,
                                            db=db)
    return updated_user


@router.put("/reject/{user_id}", response_model=User)
async def reject_user(request: Request,
                      user_id: int,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_superadmin_user)) -> User:
    """
    Reject a user by updating their status to not verified.

    Parameters:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to reject.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        User: The updated user object.

    This function rejects a user by updating their status to not verified in the
    database. The user is identified by their ID and the current user is
    authenticated using the `get_superadmin_user` dependency. The function
    returns the updated user object.
    """
    user = await check_user_for_superuser(request=request,
                                          user_id=user_id,
                                          current_user=current_user,
                                          db=db)
    updated_user = await update_user_status(request=request, user=user,
                                            current_user=current_user,
                                            is_verified=False, db=db)
    return updated_user


@router.put("/superadmin/{user_id}", response_model=User)
async def make_superadmin(request: Request,
                          user_id: int,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_superadmin_user)) -> User:
    """
    Make a user a superadmin.

    Parameters:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to make a superadmin.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        User: The updated user object.

    This function makes a user a superadmin by updating their role to "superadmin"
    in the database. The user is identified by their ID and the current user is
    authenticated using the `get_superadmin_user` dependency. The function
    returns the updated user object.
    """
    user = await check_user_for_superuser(request=request,
                                          user_id=user_id,
                                          current_user=current_user,
                                          db=db)
    updated_user = await update_user_role(request=request,
                                          current_user=current_user,
                                          user=user,
                                          role="superadmin",
                                          db=db)
    return updated_user

