from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "purchase" ALTER COLUMN "external_id" DROP DEFAULT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "purchase" ALTER COLUMN "external_id" SET DEFAULT 1;"""
