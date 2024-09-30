import os
from typing import (Dict)

import aiofiles
from fastapi import (APIRouter, Request, Depends, HTTPException, Form)
from fastapi.responses import (HTMLResponse, StreamingResponse, JSONResponse, Response)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (get_superadmin_user, get_current_user)
from app.logging_config import (log)
from app.models import Notification
from app.schemas import (User)
from app.templates import (app_templates)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def support_page(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return app_templates.TemplateResponse("support.html", {"request": request, "current_user": current_user})

@router.post("/send")
async def send_support_form(request: Request, name: str = Form(...), email: str = Form(...), subject: str = Form(...), message: str = Form(...)):
    #добавить логику отправки админам
    print("Support info: ", name, email, subject, message)
    return Response(status_code=200)
