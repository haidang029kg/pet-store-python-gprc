import asyncio
import uuid
from datetime import datetime
from typing import List, Union

from models import (
    EntityStockStatusType,
    InventoryTransactionModel,
    PurchaseItemEntityModel,
    PurchaseItemModel,
    PurchaseModel,
    TransactionType,
)
from pydantic import BaseModel
from services.utils import bulk_create_model, chunk_size_splitter
from settings import CHUNK_SIZE, TORTOISE_DEFAULT_CONN_NAME
from tortoise import Tortoise


class CreatePurchaseItemReq(BaseModel):
    product_id: uuid.UUID
    sku: str
    quantity: int
    price: int
    unique_identifier: Union[str, None] = None


class CreatePurchaseReq(BaseModel):
    id: int
    purchase_items: List[CreatePurchaseItemReq]


class CreatePurchaseItemRes(CreatePurchaseItemReq):
    id: uuid.UUID
    created: datetime
    modified: datetime


class CreatePurchaseRes(CreatePurchaseReq):
    created: datetime
    modified: datetime
    total_price: int
    total_units: int
    purchase_items: List[CreatePurchaseItemRes]


class PurchaseRes(BaseModel):
    id: int
    created: datetime
    modified: datetime
    total_price: int
    total_units: int


class GetListPurchaseRes(BaseModel):
    results: List[PurchaseRes]
    total: int


class GetLatestPurchaseIdRes(BaseModel):
    purchase_id: int


class CreatePurchaseService:
    def __init__(
        self, purchase_id: int, purchase_items: List[CreatePurchaseItemReq]
    ):
        self.purchase_id = purchase_id
        self.purchase_items = purchase_items

    async def create_purchase(self) -> PurchaseModel:
        return await PurchaseModel.create(id=self.purchase_id)

    async def create_purchase_items(self, purchase: PurchaseModel):
        items = [
            PurchaseItemModel(
                id=uuid.uuid4(),
                product_id=ele.product_id,
                purchase=purchase,
                sku=ele.sku,
                quantity=ele.quantity,
                unique_identifier=ele.unique_identifier,
                price=ele.price,
            )
            for ele in self.purchase_items
        ]
        return await PurchaseItemModel.bulk_create(items)

    @classmethod
    async def create_stock_transaction(
        cls, purchase: PurchaseModel, purchase_items: List[PurchaseItemModel]
    ):
        stocks = [
            InventoryTransactionModel(
                id=uuid.uuid4(),
                sku=ele.sku,
                product_id=ele.product_id,
                unique_identifier=ele.unique_identifier,
                quantity=ele.quantity,
                transaction_type=TransactionType.PURCHASE.value,
                purchase=purchase,
            )
            for ele in purchase_items
        ]
        return await InventoryTransactionModel.bulk_create(stocks)

    @classmethod
    async def create_purchase_item_entities(
        cls, purchase: PurchaseModel, purchase_items: List[PurchaseItemModel]
    ):
        purchase_item_entities = []
        for purchase_item in purchase_items:
            chunks = chunk_size_splitter(CHUNK_SIZE, purchase_item.quantity)
            for chunk in chunks:
                purchase_item_entities.extend(
                    [
                        PurchaseItemEntityModel(
                            id=uuid.uuid4(),
                            #
                            product_id=purchase_item.product_id,
                            sku=purchase_item.sku,
                            e_identifier=purchase_item.unique_identifier,
                            status=EntityStockStatusType.AVAILABLE.value,
                            #
                            purchase_id=purchase.id,
                            purchase_item_id=purchase_item.id,
                        )
                        for _ in range(chunk)
                    ]
                )
                if len(purchase_item_entities) >= CHUNK_SIZE:
                    await bulk_create_model(
                        PurchaseItemEntityModel,
                        purchase_item_entities,
                    )

        await bulk_create_model(
            PurchaseItemEntityModel, purchase_item_entities
        )

    @classmethod
    async def run_aggregation(
        cls, purchase: PurchaseModel, purchase_items: List[PurchaseItemModel]
    ) -> CreatePurchaseRes:
        """
        run aggregate query to get total price and total units
        """
        raw_sql = f"""
            SELECT purchase_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
            FROM purchase_item
            WHERE purchase_id = $1
            GROUP BY purchase_id
            """
        res_len, list_values = await Tortoise.get_connection(
            TORTOISE_DEFAULT_CONN_NAME
        ).execute_query(raw_sql, [purchase.id])
        if res_len != 1:
            # filter by purchase id must return only one row for list_values
            raise Exception("Something went wrong!")

        total_price, total_units = (
            list_values[0]["total_price"],
            list_values[0]["total_units"],
        )
        return CreatePurchaseRes(
            created=purchase.created,
            modified=purchase.modified,
            id=purchase.id,
            total_price=total_price,
            total_units=total_units,
            purchase_items=[
                CreatePurchaseItemRes(
                    id=ele.id,
                    created=ele.created,
                    modified=ele.modified,
                    product_id=ele.product_id,
                    sku=ele.sku,
                    quantity=ele.quantity,
                    price=ele.price,
                    unique_identifier=ele.unique_identifier,
                )
                for ele in purchase_items
            ],
        )


class GetListPurchaseService:
    def __init__(self, purchase_ids: Union[List[int], None] = None):
        self.purchase_ids = purchase_ids

    async def get_list_purchases(
        self, limit: int, offset: int
    ) -> GetListPurchaseRes:
        _selected_fields = f"""
            sub_query.purchase_id,
            sub_query.total_price,
            sub_query.total_units,
            purchase.created,
            purchase.modified
        """

        if not self.purchase_ids:
            queryset = PurchaseModel.all()
            raw_sql = f"""
            SELECT %s
            FROM (
                SELECT purchase_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
                FROM purchase_item
                GROUP BY purchase_id
                ORDER BY purchase_id DESC
                LIMIT $1
                OFFSET $2) as sub_query
            INNER JOIN purchase ON sub_query.purchase_id = purchase.id
            ORDER BY sub_query.purchase_id DESC
            """
            params = [limit, offset]
        else:
            queryset = PurchaseModel.filter(id__in=self.purchase_ids)
            len_purchase_ids = len(self.purchase_ids)

            where_clause = ", ".join(
                [f"${i + 1}" for i in range(len_purchase_ids)]
            )
            raw_sql = f"""
                SELECT %s
                FROM (
                    SELECT purchase_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
                    FROM purchase_item
                    WHERE purchase_id IN ({where_clause})
                    GROUP BY purchase_id
                    ORDER BY purchase_id DESC
                    LIMIT ${len_purchase_ids + 1}
                    OFFSET ${len_purchase_ids + 2}) as sub_query
                INNER JOIN purchase ON sub_query.purchase_id = purchase.id
                ORDER BY sub_query.purchase_id DESC
                """
            params = [str(ele) for ele in self.purchase_ids] + [
                limit,
                offset,
            ]

        total_promise = queryset.count()
        sql_promise = Tortoise.get_connection(
            TORTOISE_DEFAULT_CONN_NAME
        ).execute_query(raw_sql % _selected_fields, params)
        total, (res_len, list_values) = await asyncio.gather(
            total_promise, sql_promise
        )
        results: List[PurchaseRes] = []
        for purchase in list_values:
            results.append(
                PurchaseRes(
                    created=purchase["created"],
                    modified=purchase["modified"],
                    id=purchase["purchase_id"],
                    total_price=purchase["total_price"],
                    total_units=purchase["total_units"],
                )
            )
        return GetListPurchaseRes(results=results, total=total)


async def get_latest_purchase_id() -> GetLatestPurchaseIdRes:
    last_purchase = await PurchaseModel.all().order_by("-id").first()
    if not last_purchase:
        return GetLatestPurchaseIdRes(purchase_id=0)
    return GetLatestPurchaseIdRes(purchase_id=last_purchase.id)


async def list_purchase_items(
    purchase: PurchaseModel,
) -> List[CreatePurchaseItemRes]:
    items = await purchase.items.all()  # type: ignore
    return [
        CreatePurchaseItemRes(
            id=ele.id,
            created=ele.created,
            modified=ele.modified,
            product_id=ele.product_id,
            sku=ele.sku,
            quantity=ele.quantity,
            price=ele.price,
            purchase_id=ele.purchase_id,
            unique_identifier=ele.unique_identifier,
        )
        for ele in items
    ]
