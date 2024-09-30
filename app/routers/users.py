from fastapi import (APIRouter, Depends, Request, Form)
from fastapi.responses import (JSONResponse, RedirectResponse, HTMLResponse)
from fastapi.exceptions import (HTTPException)
from sqlalchemy import select

from sqlalchemy.ext.asyncio import (AsyncSession)

from app.database import (get_db)
from app.models import Task, Subtask
from app.schemas import (User, TaskCreate)
from app.crud import (get_users, hash_func)
from app.dependencies import (get_current_user)
from app.templates import app_templates
from app.utils import (verify_password)

router = APIRouter()



@router.get("/", response_model=list[User])
async def read_users(request: Request,
                     skip: int = 0,
                     limit: int = 10,
                     db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(get_current_user)) -> list[User] | RedirectResponse:
    """
    Get a list of all users.

    Parameters:
    - request (Request): The HTTP request object.
    - skip (int, optional): The number of users to skip. Default is 0.
    - limit (int, optional): The maximum number of users to return. Default is 10.
    - db (AsyncSession): The database session.
    - current_user (User): The current user (if signed in).

    Returns:
    - list[User]: A list of User objects, or a redirect to the login page if the user is not authenticated.

    This function retrieves a list of all users from the database and renders the 'users_list.html' template,
    passing the list of users and the current user as template variables. It also logs the
    access to the users list template.

    This function is protected by the `get_current_user` dependency, which means only signed in users can access this function.

    This function logs the access to the users list template using the `log` object. The log
    includes the type of user, the HTTP method, the current user ID, the URL, and the headers and
    query parameters of the request.

    This function is called by the route `/users` when the HTTP method is GET. The response
    class is set to `HTMLResponse`.
    """
    if current_user is None:
        return RedirectResponse("/login", 303)
    users = await get_users(skip=skip, limit=limit, db=db)
    return app_templates.TemplateResponse("users_list.html", {"request": request, "users": users})


@router.get("/me/", response_class=HTMLResponse)
async def read_user_me(request: Request,
                       current_user: User = Depends(get_current_user)):
    """
    Get the current user's profile page.

    Parameters:
    - request (Request): The HTTP request object.
    - current_user (User): The current user (if signed in).

    Returns:
    - HTMLResponse: The rendered profile.html template, passing the request and current user as template variables,
                    or a redirect to the login page if the user is not authenticated.

    This function retrieves the current user from the database and renders the 'profile.html' template,
    passing the current user as a template variable. It also logs the access to the user profile template.

    This function is protected by the `get_current_user` dependency, which means only signed in users can access this function.

    This function logs the access to the user profile template using the `log` object. The log
    includes the type of user, the HTTP method, the current user ID, the URL, and the headers and
    query parameters of the request.

    This function is called by the route `/users/me` when the HTTP method is GET. The response
    class is set to `HTMLResponse`.
    """
    if current_user is None:
        return RedirectResponse("/login", 303)
    return app_templates.TemplateResponse("profile.html", {"request": request, "current_user": current_user})


@router.post("/me/change-password", response_class=JSONResponse)
async def change_password(request: Request,
                          old_password: str = Form(...),
                          new_password: str = Form(...),
                          confirm_password: str = Form(...),
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Change the password of the currently authenticated user.

    Parameters:
    - request (Request): The HTTP request object.
    - old_password (str): The current password of the user.
    - new_password (str): The new password the user wants to set.
    - confirm_password (str): The user's confirmation of the new password.
    - db (AsyncSession): The database session.
    - current_user (User): The currently authenticated user.

    Returns:
    - JSONResponse: A JSON response indicating success or failure of the password change.

    This function checks if the current user is authenticated. If not, an HTTPException with status code 401 is raised.
    If the old password is incorrect, a JSONResponse with status code 400 and a message indicating the incorrect password is returned.
    If the new password is the same as the old password, a JSONResponse with status code 400 and a message indicating the same passwords is returned.
    If the new password and confirm password do not match, a JSONResponse with status code 400 and a message indicating the mismatch is returned.
    If all checks pass, the user's hashed password is updated in the database, the database is committed, and a JSONResponse with status code 200 and a success message is returned.
    """
    if current_user is None:
        raise HTTPException(401, "Unauthorized")
    if not verify_password(old_password, current_user.hashed_password):
        return JSONResponse(status_code=400,
                            content={"success": False, "message": "Incorrect current password"})
    new_password_hash = await hash_func(new_password)
    if verify_password(new_password, current_user.hashed_password):
        return JSONResponse(status_code=400,
                            content={"success": False, "message": "New and old passwords are the same"})
    if new_password != confirm_password:
        return JSONResponse(status_code=400,
                            content={"success": False, "message": "New passwords do not match"})

    current_user.hashed_password = new_password_hash
    db.add(current_user)
    await db.commit()

    return JSONResponse(status_code=200,
                        content={"success": True, "message": "Password successfully changed"})



