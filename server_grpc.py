import asyncio

import grpc
import settings
from generated import hello_pb2_grpc, inventory_pb2_grpc
from rpc_servicers import HelloServicer, InventoryRpcServicer
from services.logger import logger
from tortoise import Tortoise

_LISTEN_ADDRESS_TEMPLATE = f"{settings.LISTEN_ADDRESS}:%s"


async def connect_db():
    if not await settings.check_db_connection(uri=settings.DATABASE_URI):
        raise Exception("Can not connect to the database")

    logger.info("Connecting database ...")
    await Tortoise.init(config=settings.TORTOISE_ORM)
    Tortoise.get_connection("default")
    logger.info("Connected database")


async def serve():
    await connect_db()
    #
    logger.info("Starting asyncio server ...")
    server = grpc.aio.server()
    hello_pb2_grpc.add_HelloServiceServicer_to_server(HelloServicer(), server)
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryRpcServicer(), server
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
        server.add_secure_port(
            _LISTEN_ADDRESS_TEMPLATE % settings.GRPC_PORT, server_credentials
        )
    else:
        logger.info("loading insecure credentials ...")
        server.add_insecure_port(_LISTEN_ADDRESS_TEMPLATE % settings.GRPC_PORT)
    await server.start()
    logger.info(
        "Listening on port %s -TLS=%s",
        settings.GRPC_PORT,
        settings.ENABLED_TLS,
    )
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
