from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "stock" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "sku" VARCHAR(20) NOT NULL  PRIMARY KEY,
    "product_id" UUID NOT NULL REFERENCES "product" ("id") ON DELETE CASCADE
);
CREATE  INDEX "product_index" ON "stock" ("product_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "stock";"""
