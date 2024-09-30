import os
from typing import (Dict)

import aiofiles
from fastapi import (APIRouter, Request, Depends, HTTPException)
from fastapi.responses import (HTMLResponse, StreamingResponse, JSONResponse)

from app.dependencies import (get_superadmin_user)
from app.logging_config import (log)
from app.schemas import (User)
from app.templates import (app_templates)

router = APIRouter()

log_paths: Dict[str, str] = {
    "app": "/logs/app.json",
    "db": "/logs/db.json",
    "users": "/logs/users.json",
    "admins": "/logs/admins.json",
    "system": "/logs/system.json"
}


@router.get("/", response_class=HTMLResponse)
async def show_logs(request: Request,
                    current_user: User = Depends(get_superadmin_user)) -> HTMLResponse:
    """
    Read the logs and return a rendered HTML template showing the logs.

    Args:
        request (Request): The incoming request.
        current_user (User): The current user.

    Returns:
        TemplateResponse: The logs template with the log data.

    This function reads the logs and returns a rendered HTML template
    showing the logs. The log data is obtained using a dictionary of log
    paths and transformed into a list of dictionaries. The template response
    includes the request, log data, and the current user.

    This function is protected by the `get_superadmin_user` dependency, which means only users with the
    'superadmin' role can access this function.

    This function logs the access to the logs template using the `log` object. The log
    includes the type of user, the HTTP method, the current user ID, the URL, and the headers and
    query parameters of the request.

    This function is called by the route `/logs` when the HTTP method is GET. The response
    class is set to `HTMLResponse`.
    """
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params),
             ).info(f"Gained logs template")

    return app_templates.TemplateResponse("logs.html", {
        "request": request,
        "current_user": current_user,
        "log_type": "app",
        "log_content": "",
        "log_paths": log_paths
    })


@router.get("/download/{log_type}", response_class=StreamingResponse)
async def download_logs(request: Request,
                        log_type: str,
                        current_user: User = Depends(get_superadmin_user)) -> StreamingResponse:
    """
    Download logs for a specific log type.

    Args:
        request (Request): The incoming request.
        log_type (str): The type of log to download. Must be one of the keys in `log_paths`.
        current_user (User): The current user.

    Returns:
        StreamingResponse: The log file as a streaming response.

    This function is protected by the `get_superadmin_user` dependency, which means only users with the
    'superadmin' role can access this function.

    This function logs the download of the logs using the `log` object. The log
    includes the type of user, the HTTP method, the current user ID, the URL, and the headers and
    query parameters of the request.

    This function is called by the route `/download/{log_type}` when the HTTP method is GET. The response
    class is set to `StreamingResponse`.
    """
    path = log_paths.get(log_type)

    async def iter_file(path_to_log_file: str):
        async with aiofiles.open(path_to_log_file, mode='rb') as file_like:
            while True:
                chunk = await file_like.read(8192)
                if not chunk:
                    break
                yield chunk

    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params),
             ).info(f"Downloading logs for {log_type}")
    return StreamingResponse(iter_file(path), media_type="application/json",
                             headers={"Content-Disposition": f"attachment; filename={log_type}.json"})


@router.delete("/delete_all_logs", response_class=JSONResponse)
async def delete_all_logs(request: Request,
                          current_user: User = Depends(get_superadmin_user)) -> JSONResponse:
    """
    Delete all logs by truncating them to empty files.

    This function deletes all logs by truncating them to empty files.
    It iterates over all log types and paths in `log_paths`. If a log path exists,
    it opens the log file and truncates it to an empty file. If a log path does not exist,
    it skips to the next log type.

    Args:
        request (Request): The incoming request.
        current_user (User): The current user.

    Returns:
        JSONResponse: A JSON response indicating the log types that were cleared. If no logs are found,
        a JSON response indicating that no logs were found or cleared is returned.

    This function is protected by the `get_superadmin_user` dependency, which means only users with the
    'superadmin' role can access this function.

    This function logs the deletion of the logs using the `log` object. The log
    includes the type of user, the HTTP method, the current user ID, the URL, and the headers and
    query parameters of the request.

    This function is called by the route `/delete_all_logs` when the HTTP method is DELETE. The response
    class is set to `JSONResponse`.
    """
    cleared_logs = []
    for log_type, path in log_paths.items():
        try:
            if os.path.exists(path):
                async with aiofiles.open(path, 'w') as file:
                    await file.write("")
                cleared_logs.append(log_type)
                log.bind(type="admins",
                         method=request.method,
                         current_user_id=current_user.id,
                         url=str(request.url),
                         headers=dict(request.headers),
                         params=dict(request.query_params),
                         ).info(f"Delete logs for {log_type}")
        except Exception as e:
            log.bind(type="admins",
                     method=request.method,
                     current_user_id=current_user.id,
                     url=str(request.url),
                     headers=dict(request.headers),
                     params=dict(request.query_params),
                     ).info(f"Tried to delete logs for {log_type} but an error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to clear {log_type} logs: {str(e)}")

    if not cleared_logs:
        log.bind(type="admins",
                 method=request.method,
                 current_user_id=current_user.id,
                 url=str(request.url),
                 headers=dict(request.headers),
                 params=dict(request.query_params),
                 ).info(f"Tried to clear all logs, but all logs are empty")
        return JSONResponse(content={"detail": "No log files were found or cleared."}, status_code=200)
    log.bind(type="admins",
             method=request.method,
             current_user_id=current_user.id,
             url=str(request.url),
             headers=dict(request.headers),
             params=dict(request.query_params),
             ).info(f"Delete all logs")
    return JSONResponse(content={"detail": f"Cleared logs for: {', '.join(cleared_logs)}"}, status_code=200)
