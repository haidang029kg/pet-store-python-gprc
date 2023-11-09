from tortoise import fields

from .base import DbModel


class PurchaseModel(DbModel):
    id = fields.UUIDField(pk=True, default=fields.UUIDField)
    note = fields.TextField(null=True)

    class Meta:
        table = "purchase"


class PurchaseItemModel(DbModel):
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
