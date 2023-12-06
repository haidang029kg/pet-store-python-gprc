from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sale_order" ADD "status" VARCHAR(9) NOT NULL  DEFAULT 'draft';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sale_order" DROP COLUMN "status";"""
