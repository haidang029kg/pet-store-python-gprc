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


class PurchaseModel(DbModel):
    """Purchase Model
    represents a purchase from a supplier"""

    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    note = fields.TextField(null=True)

    class Meta:
        table = "purchase"


class PurchaseItemModel(DbModel):
    """PurchaseItem Model
    represents a product (sku) in a purchase"""

    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    purchase = fields.ForeignKeyField(
        "inventory.PurchaseModel",
        related_name="items",
    )

    product_id = fields.UUIDField()
    sku = fields.CharField(max_length=20)
    unique_identifier = fields.CharField(max_length=20, null=True)

    price = fields.IntField()
    quantity = fields.IntField()

    class Meta:
        table = "purchase_item"


class PurchaseItemEntityModel(DbModel):
    """PurchaseItemEntity Model
    represents a single entity of a product (sku) in the warehouse"""

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


class SaleOrderModel(DbModel):
    """SaleOrder Model
    represents a sale to a customer"""

    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    note = fields.TextField(null=True)

    class Meta:
        table = "sale_order"


class SaleOrderItemModel(DbModel):
    """SaleOrderItem Model
    represents a product (sku) in a sale"""

    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    sale_order = fields.ForeignKeyField(
        "inventory.SaleOrderModel",
        related_name="items",
    )

    product_id = fields.UUIDField()
    sku = fields.CharField(max_length=20)

    price = fields.IntField()
    quantity = fields.IntField()

    class Meta:
        table = "sale_order_item"


class SaleOrderItemEntityModel(DbModel):
    """SaleOrderItemEntity Model
    represents a single entity of a product (sku) in the warehouse that are sold to a customer
    """

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


class InventoryTransactionModel(DbModel):
    """
    InventoryTransaction Model
    represents a transaction of a product (sku) in the warehouse
    """

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
