import base64
import os
import aiofiles
from cryptography.hazmat.primitives import (serialization)
from cryptography.hazmat.primitives.asymmetric import (rsa, ec)
from cryptography.hazmat.backends import (default_backend)

from app.logging_config import (log)

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH")


async def generate_rsa_keys(regenerate: bool = False) -> None:
    """
        Asynchronously generates RSA private and public keys.

        Args:
            regenerate (bool, optional): If True, regenerates keys even if they already exist. Defaults to False.

        Returns:
            None

        Raises:
            None

        Logs:
            - If the keys are successfully generated, logs an info message.
            - If the keys are not successfully generated, logs an error message.
    """
    if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH) or regenerate is True:
        # Генерация приватного ключа
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Сохранение приватного ключа
        async with aiofiles.open(PRIVATE_KEY_PATH, "wb+") as private_file:
            await private_file.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()  # Без шифрования
                )
            )

        # Генерация публичного ключа
        public_key = private_key.public_key()

        # Сохранение публичного ключа
        async with aiofiles.open(PUBLIC_KEY_PATH, "wb+") as public_file:
            await public_file.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )
        log.bind(type="system",
                 is_regenerate=regenerate
                 ).info(f"Пара ключей сгенерирована и сохранена в файлы {PRIVATE_KEY_PATH} и {PUBLIC_KEY_PATH}")
        print(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()  # Без шифрования
                ))
        print(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
    else:
        log.bind(type="system",
                 is_regenerate=regenerate
                 ).info(f"Пара ключей уже сгенерирована и сохранена в файлы")
