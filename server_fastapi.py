import asyncio

import settings
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from tortoise import Tortoise

from fast_routers import PurchaseRouter
from fast_routers.sale_order import SaleOrderRouter

app = FastAPI()


@app.get("/health")
async def root():
    return {"message": "Hello World"}


app.include_router(PurchaseRouter(), prefix="/purchases", tags=["purchases"])
app.include_router(
    SaleOrderRouter(), prefix="/sale-orders", tags=["sale-orders"]
)
# app config
origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    if not await settings.check_db_connection(uri=settings.DATABASE_URI):
        raise Exception("Can not connect to the database")
    await Tortoise.init(config=settings.TORTOISE_ORM)


@app.on_event("shutdown")
async def shutdown():
    await Tortoise.close_connections()


async def run_command():
    await startup()
    await shutdown()


if __name__ == "__main__":
    asyncio.run(run_command())
