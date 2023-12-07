from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "purchase" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY
);
COMMENT ON TABLE "purchase" IS 'Purchase Model';
CREATE TABLE IF NOT EXISTS "purchase_item" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "product_id" UUID NOT NULL,
    "sku" VARCHAR(20) NOT NULL,
    "unique_identifier" VARCHAR(20),
    "price" INT NOT NULL,
    "quantity" INT NOT NULL,
    "purchase_id" INT NOT NULL REFERENCES "purchase" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "purchase_item" IS 'PurchaseItem Model';
CREATE TABLE IF NOT EXISTS "purchase_item_entity" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "product_id" UUID NOT NULL,
    "sku" VARCHAR(20) NOT NULL,
    "unique_identifier" VARCHAR(20),
    "status" VARCHAR(9) NOT NULL  DEFAULT 'available',
    "purchase_id" INT NOT NULL REFERENCES "purchase" ("id") ON DELETE CASCADE,
    "purchase_item_id" UUID NOT NULL REFERENCES "purchase_item" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "purchase_item_entity"."status" IS 'AVAILABLE: available\nSOLD: sold\nRETURNED: returned\nADJUSTED: adjusted';
COMMENT ON TABLE "purchase_item_entity" IS 'PurchaseItemEntity Model';
CREATE TABLE IF NOT EXISTS "sale_order" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY
);
COMMENT ON TABLE "sale_order" IS 'SaleOrder Model';
CREATE TABLE IF NOT EXISTS "inventory_transaction" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "product_id" UUID NOT NULL,
    "sku" VARCHAR(20) NOT NULL,
    "unique_identifier" VARCHAR(20),
    "quantity" INT NOT NULL,
    "transaction_type" VARCHAR(10) NOT NULL  DEFAULT 'purchase',
    "purchase_id" INT REFERENCES "purchase" ("id") ON DELETE CASCADE,
    "sale_order_id" INT REFERENCES "sale_order" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "inventory_transaction"."transaction_type" IS 'PURCHASE: purchase\nSALE: sale\nRETURN: return\nADJUSTMENT: adjustment';
COMMENT ON TABLE "inventory_transaction" IS 'InventoryTransaction Model';
CREATE TABLE IF NOT EXISTS "sale_order_item" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "product_id" UUID NOT NULL,
    "sku" VARCHAR(20) NOT NULL,
    "price" INT NOT NULL,
    "quantity" INT NOT NULL,
    "sale_order_id" INT NOT NULL REFERENCES "sale_order" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "sale_order_item" IS 'SaleOrderItem Model';
CREATE TABLE IF NOT EXISTS "sale_order_item_entity" (
    "created" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "modified" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" UUID NOT NULL  PRIMARY KEY,
    "purchase_item_entity_id" UUID NOT NULL REFERENCES "purchase_item_entity" ("id") ON DELETE CASCADE,
    "sale_order_id" INT NOT NULL REFERENCES "sale_order" ("id") ON DELETE CASCADE,
    "sale_order_item_id" UUID NOT NULL REFERENCES "sale_order_item" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "sale_order_item_entity" IS 'SaleOrderItemEntity Model';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
