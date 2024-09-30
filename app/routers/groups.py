# from fastapi import APIRouter, Depends, HTTPException, Request, Form
# from fastapi.responses import RedirectResponse, Response, JSONResponse
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
#
# from app.dependencies import get_current_user
# from app.models import User
# from app.database import get_db
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
#
# from app.schemas import TaskCreate
#
# router = APIRouter()
#
# templates = Jinja2Templates(directory="app/templates")
#
# # Страница создания новой группы
# @router.get("/create", response_class=HTMLResponse)
# async def create_group_page(request: Request, current_user: User = Depends(get_current_user)):
#     return templates.TemplateResponse("group_create.html", {"request": request})
#
# # Создание новой группы (обработка формы)
# @router.post("/create")
# async def create_group(name: str = Form(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
#     new_group = Group(name=name, creator_id=current_user.id)
#     new_group.members.append(current_user)  # Создатель группы автоматически становится участником
#     db.add(new_group)
#     try:
#         await db.commit()  # Коммит изменений в базу данных
#         return RedirectResponse(url=f"/groups/{new_group.id}/admin", status_code=303)  # Возвращаем результат
#     except Exception as e:
#         await db.rollback()  # Откат транзакции в случае ошибки
#         raise HTTPException(status_code=500, detail=str(e))
#
# # Список групп текущего пользователя
# @router.get("/", response_class=HTMLResponse)
# async def get_groups(request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
#     groups = await db.execute(select(Group).where(Group.members.contains(current_user)))
#     groups_list = groups.scalars().all()
#     return templates.TemplateResponse("group_list.html", {"request": request, "groups": groups_list})