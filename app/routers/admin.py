import os

from fastapi import (APIRouter,
                     Depends,
                     Request)
from fastapi.responses import (JSONResponse,
                               HTMLResponse)
from fastapi.exceptions import HTTPException
from sqlalchemy import select

from sqlalchemy.ext.asyncio import (AsyncSession)

from app.models import Task, Subtask, User, Notification
from app.templates import (app_templates)
from app.logging_config import (log)
from app.database import (get_db)
from app.schemas import (TaskCreate)
from app.crud import (update_user_role,
                      block_user,
                      unblock_user,
                      update_user,
                      user_to_dict,
                      get_all_users,
                      get_unblocked_users,
                      get_blocked_users,
                      get_unverified_users, send_notification)
from app.dependencies import (get_admin_user,
                              check_user,
                              check_user_for_superuser)

router = APIRouter()


@router.get("/panel", response_class=HTMLResponse)
async def admin_panel(request: Request,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_admin_user)) -> HTMLResponse:
    """
        Endpoint for the admin panel.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): The database session.
            current_user (User): The current user.

        Returns:
            TemplateResponse: The rendered admin panel HTML template.

        Logs:
            - Logs an info message indicating that the admin panel has been accessed.
    """

    public_vapid_key = os.getenv("VAPID_PUBLIC_KEY")

    all_users = await get_all_users(request=request, current_user=current_user, db=db)
    unblocked_users = await get_unblocked_users(request=request, current_user=current_user, db=db)
    blocked_users = await get_blocked_users(request=request, current_user=current_user, db=db)
    unverified_users = []
    if current_user.is_superuser or current_user.role == "admin":
        unverified_users = await get_unverified_users(request=request, current_user=current_user, db=db)
    print("loll", unverified_users)
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params)
             ).info(f"Gained access to admin panel")
    return app_templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "current_user": current_user,
        "all_users": all_users,
        "unblocked_users": unblocked_users,
        "blocked_users": blocked_users,
        "unverified_users": unverified_users,

        "public_vapid_key": public_vapid_key
    })


@router.put("/role/{user_id}")
async def change_user_role(request: Request,
                           user_id: int,
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_admin_user)):
    """
    Change the role of a user in the database.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user whose role is to be changed.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        User: The updated user object.

    Raises:
        HTTPException: If the user is not found.

    Logs:
        - Logs an info message indicating the updated user role.
    """
    user = await check_user(request=request, user_id=user_id,
                            current_user=current_user, db=db)

    data = await request.json()

    updated_user = await update_user_role(request=request, current_user=current_user,
                                          user=user, role=data["role"], db=db)
    return updated_user


@router.get("/user/{user_id}", response_class=JSONResponse)
async def get_user_details(request: Request,
                           user_id: int,
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_admin_user)) -> JSONResponse:

    """
    Get details of a user by their ID.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to retrieve.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        JSONResponse: A JSON response containing the user details.

    Raises:
        HTTPException: If the user is not found.
    """
    user = await check_user(request=request, user_id=user_id,
                            current_user=current_user, db=db)
    user_data = user_to_dict(user)

    return JSONResponse(content=user_data)


@router.put("/user/{user_id}", response_class=JSONResponse)
async def update_user_details(request: Request,
                              user_id: int,
                              user_data: dict,
                              current_user: User = Depends(get_admin_user),
                              db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Update the details of a user in the database.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to update.
        user_data (dict): The updated user data.
        current_user (User): The current user.
        db (AsyncSession): The database session.

    Returns:
        JSONResponse: A JSON response containing the updated user details.

    Raises:
        HTTPException: If the user is not found.
    """
    user = await check_user(request=request, user_id=user_id,
                            current_user=current_user, db=db)
    updated_user = await update_user(request=request, current_user=current_user,
                                     user=user, user_data=user_data, db=db)
    user_data = user_to_dict(updated_user)

    return JSONResponse(content=user_data)


@router.put("/block/{user_id}")
async def block_user_route(request: Request,
                           user_id: int,
                           db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_admin_user)):

    """
    Block a user.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to block.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        User: The blocked user.

    Raises:
        HTTPException: If the user is not found.

    """
    user = await check_user_for_superuser(request=request, user_id=user_id,
                                          current_user=current_user, db=db)
    blocked_user = await block_user(request=request, current_user=current_user,
                                    user=user, db=db)

    return blocked_user


@router.put("/unblock/{user_id}")
async def unblock_user_route(request: Request,
                             user_id: int,
                             db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_admin_user)):
    """
    Unblock a user.

    Args:
        request (Request): The HTTP request object.
        user_id (int): The ID of the user to unblock.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        User: The unblocked user.

    Raises:
        HTTPException: If the user is not found.

    """
    user = await check_user_for_superuser(request=request, user_id=user_id,
                                          current_user=current_user, db=db)
    unblocked_user = await unblock_user(request=request, current_user=current_user,
                                        user=user, db=db)

    return unblocked_user


@router.post("/add-task/{user_id}")
async def create_task_for_user(user_id: int, task: TaskCreate, current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_task = Task(user_id=user_id, name=task.name, assigner_id=current_user.id, description=task.description, deadline=task.deadline)
    db.add(db_task)
    await db.flush()

    # Добавляем подпункты
    for subtask_data in task.subtasks:
        db_subtask = Subtask(task_id=db_task.id, name=subtask_data.name)
        db.add(db_subtask)

    new_notification = Notification(
        user_id=user_id,
        task_id=db_task.id,
        content=f"New ask: '{db_task.name}'.",
        type="started",
    )
    db.add(new_notification)
    await db.flush()

    await db.commit()

    await send_notification(db_user.phone_number, f"New task: {db_task.name}")

    return db_task


@router.get("/add-task", response_class=HTMLResponse)
async def add_task_page(request: Request, current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    # Получение всех пользователей из базы данных
    result = await db.execute(select(User))
    users = result.scalars().all()

    # Преобразуем пользователей в формат словаря для передачи на клиент
    users_data = {
        user.id: {
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        for user in users
    }

    return app_templates.TemplateResponse("add_task.html", {"request": request, "current_user": current_user, "users": users_data})