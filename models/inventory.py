from enum import Enum

from tortoise import fields, models

from .base import DbModel


class TransactionType(Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"


class ProductModel(DbModel):
    id = fields.UUIDField(pk=True)

    class Meta:
        table = "product"


class StockModel(DbModel):
    sku = fields.CharField(max_length=20, pk=True)
    product = fields.ForeignKeyField(
        "inventory.ProductModel",
        related_name="stocks",
    )

    class Meta:
        table = "stock"

        # add index to product foreign key
        indexes = [
            models.Index(fields=["product_id"], name="product_index"),
        ]


class StockTransactionModel(DbModel):
    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    stock = fields.ForeignKeyField(
        "inventory.StockModel",
        related_name="transactions",
    )
    quantity = fields.IntField()
    #
    transaction_type = fields.CharEnumField(
        TransactionType, default=TransactionType.PURCHASE.value
    )
    #
    note = fields.TextField(null=True)

    class Meta:
        table = "stock_transaction"
        indexes = [
            models.Index(
                fields=["stock_id", "transaction_type"],
                name="sku_transaction_type_index",
            ),
        ]
