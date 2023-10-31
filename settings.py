import os

from dotenv import load_dotenv

#
load_dotenv()
#
ENABLED_TLS = os.environ.get("ENABLED_TLS", "False") in ["True", "true", "1"]
GRPC_PORT = os.environ.get("GRPC_PORT", "50051")
#
DATABASE_URI = os.environ.get("DATABASE_URI")
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URI},
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


def _load_credential_from_file(filepath):
    real_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(real_path, "rb") as f:
        print(f"Loading credential from {real_path}")
        return f.read()


if ENABLED_TLS is True:
    # Credentials env names
    SERVER_CERTIFICATE_FILE_PATH = os.environ.get("SERVER_CERTIFICATE_FILE_PATH",
                                                  default="credentials/example_localhost.crt")
    SERVER_CERTIFICATE_KEY_FILE_PATH = os.environ.get("SERVER_CERTIFICATE_KEY_FILE_PATH",
                                                      default="credentials/example_localhost.key")
    ROOT_CERTIFICATE_FILE_PATH = os.environ.get("ROOT_CERTIFICATE_FILE_PATH", default="credentials/example_root.crt")
    # Load credentials
    SERVER_CERTIFICATE = _load_credential_from_file(SERVER_CERTIFICATE_FILE_PATH)
    SERVER_CERTIFICATE_KEY = _load_credential_from_file(SERVER_CERTIFICATE_KEY_FILE_PATH)
    ROOT_CERTIFICATE = _load_credential_from_file(ROOT_CERTIFICATE_FILE_PATH)
