from enum import Enum

from tortoise import fields

from .base import DbModel


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"


class EntityStockStatusType(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    RETURNED = "returned"
    ADJUSTED = "adjusted"


class InventoryTransactionModel(DbModel):
    id = fields.UUIDField(pk=True, default=fields.UUIDField)

    product_id = fields.UUIDField()
    sku = fields.CharField(max_length=20)
    unique_identifier = fields.CharField(max_length=20, null=True)

    quantity = fields.IntField()

    transaction_type = fields.CharEnumField(
        TransactionType, default=TransactionType.PURCHASE.value
    )

    purchase = fields.ForeignKeyField(
        "inventory.PurchaseModel",
        related_name="stock_transactions",
        null=True,
    )
    sale_order = fields.ForeignKeyField(
        "inventory.SaleOrderModel",
        related_name="stock_transactions",
        null=True,
    )

    class Meta:
        table = "inventory_transaction"


class PurchaseItemEntityModel(DbModel):
    id = fields.UUIDField(pk=True, default=fields.UUIDField)

    product_id = fields.UUIDField()
    sku = fields.CharField(max_length=20)
    unique_identifier = fields.CharField(max_length=20, null=True)

    status = fields.CharEnumField(
        EntityStockStatusType, default=EntityStockStatusType.AVAILABLE.value
    )

    purchase = fields.ForeignKeyField(
        "inventory.PurchaseModel",
        related_name="entity_stocks",
    )
    purchase_item = fields.ForeignKeyField(
        "inventory.PurchaseItemModel",
        related_name="entity_stocks",
    )

    class Meta:
        table = "purchase_item_entity"


class SaleOrderItemEntityModel(DbModel):
    id = fields.UUIDField(pk=True, default=fields.UUIDField)

    purchase_item_entity = fields.ForeignKeyField(
        "inventory.PurchaseItemEntityModel",
        related_name="sale_order_item_entities",
    )
    sale_order = fields.ForeignKeyField(
        "inventory.SaleOrderModel",
        related_name="sale_order_item_entities",
    )
    sale_order_item = fields.ForeignKeyField(
        "inventory.SaleOrderItemModel",
        related_name="sale_order_item_entities",
    )

    class Meta:
        table = "sale_order_item_entity"
