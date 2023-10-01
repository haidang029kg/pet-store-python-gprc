from tortoise import fields
from tortoise.models import Model


class DbModel(Model):
    created = fields.DatetimeField(auto_now_add=True)
    modified = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True
