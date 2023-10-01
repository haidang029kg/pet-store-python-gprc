import os

from dotenv import load_dotenv

#
load_dotenv()
#
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
