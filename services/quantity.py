import uuid
from typing import List, Union

from models import InventoryTransactionModel
from pydantic import BaseModel
from tortoise.functions import Sum


class SkuQuantity(BaseModel):
    product_id: uuid.UUID
    sku: str
    quantity: int


class GetQuantityRes(BaseModel):
    results: List[SkuQuantity]


async def get_quantity(
    product_id: Union[uuid.UUID, None] = None,
    skus: Union[List[str], None] = None,
) -> GetQuantityRes:
    assert product_id or skus, "product_id or skus must be provided"

    if skus:
        queryset = InventoryTransactionModel.filter(sku__in=skus)
    else:
        queryset = InventoryTransactionModel.filter(product_id=product_id)

    # run aggregate query
    agg = (
        await queryset.annotate(total_quantity=Sum("quantity"))
        .group_by("product_id", "sku")
        .values("product_id", "sku", "total_quantity")
    )
    if not agg:
        results = []
    else:
        results = [
            SkuQuantity(
                product_id=ele.get("product_id"),
                sku=ele.get("sku"),
                quantity=ele.get("total_quantity"),
            )
            for ele in agg
        ]
    return GetQuantityRes(results=results)
