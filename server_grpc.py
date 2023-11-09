import asyncio

import grpc
from tortoise import Tortoise

import settings
from generated import inventory_pb2_grpc
from rpc_servicers import InventoryServicer
from services import logger

_LISTEN_ADDRESS_TEMPLATE = f'{settings.LISTEN_ADDRESS}:%s'


async def connect_db():
    logger.info("Connecting database ...")
    await Tortoise.init(config=settings.TORTOISE_ORM)
    Tortoise.get_connection("default")
    logger.info("Connected database")


async def serve():
    await connect_db()
    #
    logger.info("Starting asyncio server ...")
    server = grpc.aio.server()
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryServicer(), server
    )

    if settings.ENABLED_TLS is True:
        # Loading credentials
        logger.info("Loading credentials ...")
        server_credentials = grpc.ssl_server_credentials(
            (
                (
                    settings.SERVER_CERTIFICATE_KEY,
                    settings.SERVER_CERTIFICATE,
                ),
            )
        )
        server.add_secure_port(_LISTEN_ADDRESS_TEMPLATE % settings.GRPC_PORT, server_credentials)
    else:
        logger.info("loading insecure credentials ...")
        server.add_insecure_port(_LISTEN_ADDRESS_TEMPLATE % settings.GRPC_PORT)
    await server.start()
    logger.info("Listening on port %s -TLS=%s", settings.GRPC_PORT, settings.ENABLED_TLS)
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
