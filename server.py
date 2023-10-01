import asyncio

import grpc
from tortoise import Tortoise

import settings
from generated import inventory_pb2_grpc
from rpc_servicers import InventoryServicer
from services import logger


async def connect_db():
    logger.info("Connecting database ...")
    await Tortoise.init(config=settings.TORTOISE_ORM)
    Tortoise.get_connection("default")
    logger.info("Connected database")

    # await Tortoise.generate_schemas()


async def serve():
    await connect_db()
    #
    logger.info("Starting asyncio server ...")
    server = grpc.aio.server()
    inventory_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryServicer(), server
    )
    port = settings.GRPC_PORT
    insecure_port = f"[::]:{port}"
    server.add_insecure_port(insecure_port)
    logger.info("Listening on insecure port %s", insecure_port)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
