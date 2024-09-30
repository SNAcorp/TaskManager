import os
from typing import (Dict)

import aiofiles
from fastapi import (APIRouter, Request, Depends, HTTPException)
from fastapi.responses import (HTMLResponse, StreamingResponse, JSONResponse)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (get_superadmin_user, get_current_user)
from app.jwt_auth import verify_notification_token, generate_notification_token
from app.logging_config import (log)
from app.models import Notification
from app.schemas import (User)
from app.templates import (app_templates)

router = APIRouter()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
@router.get("/", response_class=JSONResponse)
async def get_notifications(
    skip: int = 0,
    limit: int = 15,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.creation_date.desc())
        .offset(skip)
        .limit(limit)
    )
    notifications = result.scalars().all()

    # Отметить уведомления как прочитанные
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
    await db.commit()

    return notifications

@router.get("/check_unread")
async def check_unread_notifications(user_id: int, session: AsyncSession = Depends(get_db)):
    # Выполняем запрос для проверки наличия хотя бы одного непрочитанного уведомления
    result = await session.execute(
        select(Notification)
        .filter(Notification.user_id == user_id)
        .filter(Notification.is_read == False)
        .limit(1)  # Ограничиваем результат одним уведомлением, так как нам важно лишь его наличие
    )
    unread_notification = result.scalars().first()

    if unread_notification:
        return {"has_unread": True}
    else:
        return {"has_unread": False}

@router.post("/check")
async def check_notification_token(user_telegram_id: int, token: str):
    # if bot_token != BOT_TOKEN:
    #     raise HTTPException(status_code=401, detail="Invalid bot token")

    if await verify_notification_token(token=token, user_telegram_id=user_telegram_id):
        return JSONResponse({"is_valid": True})

    return JSONResponse({"is_valid": False})

@router.get("/start_notifications")
async def start_notifications(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    token = generate_notification_token(application_user_id=str(current_user.id))
    bot_link = f"https://t.me/sna_notification_bot"
    return {"bot_link": bot_link}
