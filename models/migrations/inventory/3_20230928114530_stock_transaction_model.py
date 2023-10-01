from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "stock_transaction" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "quantity" INT NOT NULL,
    "transaction_type" VARCHAR(10) NOT NULL  DEFAULT 'purchase',
    "note" TEXT,
    "stock_id" VARCHAR(20) NOT NULL REFERENCES "stock" ("sku") ON DELETE CASCADE
);
CREATE  INDEX "sku_transaction_type_index" ON "stock_transaction" ("stock_id", "transaction_type");
COMMENT ON COLUMN "stock_transaction"."transaction_type" IS 'PURCHASE: purchase\nSALE: sale\nRETURN: return\nADJUSTMENT: adjustment';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "stock_transaction";
    """
