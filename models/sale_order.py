from tortoise import fields

from .base import DbModel


class SaleOrderModel(DbModel):
    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    note = fields.TextField(null=True)

    class Meta:
        table = "sale_order"


class SaleOrderItemModel(DbModel):
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
