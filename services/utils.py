from typing import List, Type, Union

from models import PurchaseItemEntityModel, SaleOrderItemEntityModel


async def bulk_create_model(
    model: Union[
        Type[PurchaseItemEntityModel], Type[SaleOrderItemEntityModel]
    ],
    items: List[Union[PurchaseItemEntityModel, SaleOrderItemEntityModel]],
):
    if items:
        await model.bulk_create(items)
        items.clear()


def chunk_size_splitter(chunk_size: int, number_value: int) -> List[int]:
    if number_value < chunk_size:
        return [number_value]

    left_part = int(number_value / chunk_size)
    right_part = number_value % chunk_size
    res = [chunk_size] * left_part
    if right_part:
        res.append(right_part)
    return res
