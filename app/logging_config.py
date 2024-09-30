from typing import (Dict)
from loguru import (logger)

# Определение путей к файлам логов
log_paths: Dict[str, str] = {
    "app": "/logs/app.json",
    "db": "/logs/db.json",
    "users": "/logs/users.json",
    "admins": "/logs/admins.json",
    "terminals": "/logs/terminals.json",
    "system": "/logs/system.json"
}

log = logger


def configure_logging() -> None:
    """
    Configures logging for different log types.

    This function sets up logging for each log type defined in `log_paths`.
    It adds a log file for each log type, with a maximum log file size of 1 day
    and a maximum retention of 7 days. Logging is set to DEBUG level, and logs
    are serialized to JSON format. Logging is also asynchronous and includes
    full backtraces and diagnostic information. Each log file is filtered to
    only include records with a "type" key matching the log type.

    Parameters:
    None

    Returns:
    None
    """
    for log_type, path in log_paths.items():
        log.add(
            path,
            rotation="1 day",
            retention="7 days",
            level="DEBUG",
            serialize=True,  # Логирование в формате JSON
            enqueue=True,  # Асинхронное логирование
            backtrace=True,  # Полные трейсы ошибок
            diagnose=True,  # Подробная диагностика
            filter=lambda record, log_type=log_type: record["extra"].get("type") == log_type
        )
    print("logger was configured successfully")


configure_logging()
