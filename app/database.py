import os
import asyncio

import redis.asyncio as redis
from sqlalchemy import (text)
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession)
from sqlalchemy.orm import (sessionmaker)
from sqlalchemy.exc import (SQLAlchemyError, IntegrityError, OperationalError)

from app.logging_config import (log)


DATABASE_URL = os.getenv('DATABASE_URL')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False,
                            expire_on_commit=False,
                            bind=engine,
                            class_=AsyncSession)
MAX_RETRIES = 5

redis_client = None

async def load_redis():
    global redis_client
    redis_client = await redis.Redis(host=f"{REDIS_HOST}://localhost", port=int(REDIS_PORT), decode_responses=True)


async def get_db() -> AsyncSession:
    """
    Asynchronously establishes and returns a database session.

    This function creates a new database session using the asynchronous session factory `SessionLocal`.
    It logs the start of the session and begins a transaction. It then enters a loop that retries the transaction
    up to a maximum number of times (`MAX_RETRIES`). If an exception of type `IntegrityError` or `OperationalError`
    occurs, the transaction is rolled back and the loop retries the transaction after an exponentially increasing delay.
    If any other type of exception occurs, the transaction is rolled back and an error message is logged. If the maximum
    number of retries is reached, an error message logged and the function raises the exception. If the transaction
    is successful, it is committed and a success message logged. Finally, the session closed and a close message
    logged.

    Returns:
        AsyncSession: The database session.

    Raises:
        Any exception that occurs during the transaction, including `IntegrityError`, `OperationalError`, and
        `SQLAlchemyError`.
    """
    async with SessionLocal() as session:
        log.bind(type="db").info("Database session started")
        retries = 0
        try:
            while retries < MAX_RETRIES:
                try:
                    async with session.begin():
                        # Устанавливаем уровень изоляции транзакции на максимально строгий
                        await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
                        yield session
                        log.bind(type="db").info("Database session successfully committed")
                        break  # Выходим из цикла при успешной транзакции
                except IntegrityError as e:
                    await session.rollback()  # Откат транзакции при конфликте версий
                    retries += 1
                    log.bind(type="db").warning(
                        f"IntegrityError: Collision detected and transaction rolled back. Retrying {retries}/{MAX_RETRIES}..."
                    )
                    if retries >= MAX_RETRIES:
                        log.bind(type="db").error(
                            f"Transaction failed after {MAX_RETRIES} attempts. Aborting."
                        )
                        raise  # Повторное возбуждение исключения после достижения лимита попыток
                    await asyncio.sleep(
                        2 ** retries)  # Экспоненциальное увеличение времени ожидания перед повторной попыткой
                except OperationalError as e:
                    await session.rollback()  # Откат транзакции в случае операционной ошибки
                    retries += 1
                    log.bind(type="db").warning(
                        f"OperationalError: Retry {retries}/{MAX_RETRIES}..."
                    )
                    if retries >= MAX_RETRIES:
                        log.bind(type="db").error(
                            f"Transaction failed after {MAX_RETRIES} attempts. Aborting."
                        )
                        raise
                    await asyncio.sleep(2 ** retries)  # Экспоненциальная задержка перед повторной попыткой
                except SQLAlchemyError as e:
                    await session.rollback()  # Откат транзакции в случае других ошибок SQLAlchemy
                    log.bind(type="db").error(f"Database session rollback due to error: {str(e)}")
                    raise  # Повторное возбуждение исключения для дальнейшей обработки
            else:
                log.bind(type="db").error("Max retries reached, transaction aborted.")
        finally:
            log.bind(type="db").info("Database session closed")
