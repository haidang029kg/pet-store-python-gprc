import os

import asyncpg
from dotenv import load_dotenv

#
load_dotenv()
#
ENABLED_TLS: bool = os.environ.get("ENABLED_TLS", "False") in [
    "True",
    "true",
    "1",
]
LISTEN_ADDRESS = os.environ.get("LISTEN_ADDRESS", "0.0.0.0")
GRPC_PORT = os.environ.get("GRPC_PORT", "50051")
#
DATABASE_URI = os.environ.get("DATABASE_URI")
TORTOISE_DEFAULT_CONN_NAME = os.environ.get(
    "TORTOISE_DEFAULT_CONN_NAME", "default"
)
TORTOISE_ORM = {
    "connections": {TORTOISE_DEFAULT_CONN_NAME: DATABASE_URI},
    "apps": {
        "inventory": {
            "models": [
                "aerich.models",
                #
                "models",
            ],
            "default_connection": "default",
        },
    },
}
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "5000"))


def _load_credential_from_file(filepath):
    real_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(real_path, "rb") as f:
        print(f"Loading credential from {real_path}")
        return f.read()


if ENABLED_TLS is True:
    # Credentials env names
    SERVER_CERTIFICATE_FILE_PATH = os.environ.get(
        "SERVER_CERTIFICATE_FILE_PATH",
        default="credentials/example_localhost.crt",
    )
    SERVER_CERTIFICATE_KEY_FILE_PATH = os.environ.get(
        "SERVER_CERTIFICATE_KEY_FILE_PATH",
        default="credentials/example_localhost.key",
    )
    ROOT_CERTIFICATE_FILE_PATH = os.environ.get(
        "ROOT_CERTIFICATE_FILE_PATH", default="credentials/example_root.crt"
    )
    # Load credentials
    SERVER_CERTIFICATE = _load_credential_from_file(
        SERVER_CERTIFICATE_FILE_PATH
    )
    SERVER_CERTIFICATE_KEY = _load_credential_from_file(
        SERVER_CERTIFICATE_KEY_FILE_PATH
    )
    ROOT_CERTIFICATE = _load_credential_from_file(ROOT_CERTIFICATE_FILE_PATH)


async def check_db_connection(uri: str) -> bool:
    try:
        connection = await asyncpg.connect(uri)
        connection.get_settings()
        await connection.close()
        return True
    except Exception as error:
        print(error)
        return False
