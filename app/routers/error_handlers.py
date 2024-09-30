# error_handlers.py
from fastapi import Request, HTTPException, Depends
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import HTMLResponse, RedirectResponse, Response

from app.dependencies import get_current_user
from app.schemas import User
from app.templates import app_templates


async def custom_404_handler(request: Request,
                             exc: HTTPException,
                             current_user: User = Depends(get_current_user)) -> HTMLResponse:
    """
    Custom 404 error handler for FastAPI.

    Args:
        request (Request): The incoming request.
        exc (HTTPException): The exception that caused the 404 error.
        current_user (User, optional): The current user. Defaults to None.

    Returns:
        HTMLResponse: The rendered 404 error template with the request and current user.

    This function is called when a 404 error occurs in the application. It returns the rendered 404 error
    template with the request and current user. The template is located in the `app/templates` directory and is
    named `404.html`.
    """
    return app_templates.TemplateResponse("404.html", {"request": request,
                                                       "current_user": current_user}, status_code=404)


async def custom_403_handler(request: Request,
                             exc: HTTPException,
                             current_user: User = Depends(get_current_user)) -> HTMLResponse:
    """
    Custom 403 error handler for FastAPI.

    Args:
        request (Request): The incoming request.
        exc (HTTPException): The exception that caused the 403 error.
        current_user (User, optional): The current user. Defaults to None.

    Returns:
        HTMLResponse: The rendered 403 error template with the request and current user.

    This function is called when a 403 error occurs in the application. It returns the rendered 403 error
    template with the request and current user. The template is located in the `app/templates` directory and is
    named `403.html`.
    """
    return app_templates.TemplateResponse("403.html", {"request": request}, status_code=403)


async def custom_401_handler(request: Request,
                             exc: HTTPException,
                             current_user: User = Depends(get_current_user)) -> RedirectResponse | HTMLResponse:
    """
    Custom 401 error handler for FastAPI.

    Args:
        request (Request): The incoming request.
        exc (HTTPException): The exception that caused the 401 error.
        current_user (User, optional): The current user. Defaults to None.

    Returns:
        Union[RedirectResponse, TemplateResponse]: If the request URL path is not "/auth/login", a redirect
        response to "/auth/login" with a status code of 303 is returned. Otherwise, a rendered login/register
        template with the request is returned.

    This function is called when a 401 error occurs in the application. If the request URL path is not "/auth/login",
    a redirect response to "/auth/login" with a status code of 303 is returned. Otherwise, a rendered login/register
    template with the request is returned.
    """
    if request.url.path != "/auth/login":
        return RedirectResponse("/auth/login", status_code=303)
    else:
        return app_templates.TemplateResponse("login_register.html",
                                              {"request": request}, status_code=401)


async def custom_402_handler(request: Request,
                             exc: HTTPException,
                             current_user: User = Depends(get_current_user)) -> HTMLResponse:

    return app_templates.TemplateResponse("402.html",
                                              {"request": request, "current_user": current_user}, status_code=402)
