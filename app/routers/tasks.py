from fastapi import (APIRouter, Depends, Request, Form)
from fastapi.responses import (JSONResponse, RedirectResponse, HTMLResponse)
from fastapi.exceptions import (HTTPException)
from sqlalchemy import select

from sqlalchemy.ext.asyncio import (AsyncSession)
from sqlalchemy.orm import selectinload

from app.database import (get_db)
from app.models import Task, Subtask, User, Notification
from app.schemas import (TaskCreate, TaskUpdate)
from app.crud import (get_users, hash_func, send_notifications)
from app.dependencies import (get_current_user, get_admin_user)
from app.templates import app_templates
from app.utils import (verify_password)
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def user_tasks(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.id == current_user.id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(Task).filter(Task.user_id == current_user.id))
    tasks = result.scalars().all()

    return app_templates.TemplateResponse("tasks.html", {"request": request, "user": user, "tasks": tasks, "current_user": current_user})

@router.get("/create-task", response_class=HTMLResponse)
async def create_task(request: Request, current_user: User = Depends(get_admin_user)):
    return app_templates.TemplateResponse("create_task.html", {"request": request, "current_user": current_user})

@router.get("/{task_id}", response_class=HTMLResponse)
async def task_detail(request: Request, task_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks))  # Загружаем связанные данные (subtasks)
        .filter(Task.id == task_id)
    )
    task = result.scalars().first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return app_templates.TemplateResponse("task_detail.html", {"request": request,
                                                               "current_user": current_user,
                                                               "subtasks": [{"id": st.id, "name": st.name,
                                                                             "is_completed": st.is_completed
                                                                             } for st in task.subtasks],
                                                               "task": task})

@router.post("/task/{task_id}/complete")
async def complete_task(task_id: int, current_user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks))  # Загружаем связанные данные (subtasks)
        .filter(Task.id == task_id)
    )
    db_task = result.scalars().first()

    for subtask in db_task.subtasks:
        if not subtask.is_completed:
            raise HTTPException(status_code=400, detail="Some subtasks are not completed")

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Создание уведомления о новой задаче
    new_notification = Notification(
        user_id=db_task.assigner_id,
        task_id=db_task.id,
        content=f"Task '{db_task.name}' has been completed.",
        type="complited",
    )
    db.add(new_notification)
    await db.flush()

    db_task.is_completed = not db_task.is_completed
    await db.commit()
    result = await db.execute(select(User).filter(User.id == db_task.assigner_id))
    assigner = result.scalars().first()
    result = await db.execute(select(User).filter(User.id == db_task.assigner_id))
    user = result.scalars().first()
    await send_notifications({assigner.phone_number: f"Task: '{db_task.name}' has been completed",
                              user.phone_number: f"Task '{db_task.name}' has been completed"})
    return {"message": "Task completed successfully"}


@router.post("/subtask/{subtask_id}/complete")
async def complete_subtask(subtask_id: int, current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subtask).filter(Subtask.id == subtask_id))
    db_subtask = result.scalars().first()

    if db_subtask is None:
        raise HTTPException(status_code=404, detail="Subtask not found")

    db_subtask.is_completed = not db_subtask.is_completed
    await db.commit()
    return {"message": "Subtask updated successfully"}