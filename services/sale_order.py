import asyncio
import uuid
from datetime import datetime
from typing import List, Union

from models import (
    EntityStockStatusType,
    InventoryTransactionModel,
    PurchaseItemEntityModel,
    SaleOrderItemEntityModel,
    SaleOrderItemModel,
    SaleOrderModel,
    SaleOrderStatusType,
    TransactionType,
)
from pydantic import BaseModel
from services.utils import bulk_create_model
from settings import CHUNK_SIZE, TORTOISE_DEFAULT_CONN_NAME
from tortoise import Tortoise


class SaleItemReq(BaseModel):
    product_id: uuid.UUID
    sku: str
    quantity: int
    price: int
    unique_identifier: Union[str, None] = None


class CreateSaleOrderReq(BaseModel):
    id: int
    sale_items: List[SaleItemReq]


class SaleItemRes(SaleItemReq):
    id: uuid.UUID
    created: datetime
    modified: datetime


class CreateSaleOrderRes(CreateSaleOrderReq):
    created: datetime
    modified: datetime
    total_price: int
    total_units: int
    sale_items: List[SaleItemRes]
    status: SaleOrderStatusType


class SaleOrderRes(BaseModel):
    id: int
    created: datetime
    modified: datetime
    status: SaleOrderStatusType


class SaleOrderResV2(SaleOrderRes):
    total_price: int
    total_units: int


class GetListSaleOrderRes(BaseModel):
    results: List[SaleOrderResV2]
    total: int


class CreateSaleOrderService:
    def __init__(self, data: CreateSaleOrderReq):
        self.sale_id = data.id
        self.sale_items = data.sale_items

    async def create(self) -> CreateSaleOrderRes:
        sale_order = await self.create_sale_order()
        sale_order_items = await self.create_sale_items(sale_order)
        await self.add_transaction(sale_order, sale_order_items)
        agg_res = await self.run_aggregation(sale_order, sale_order_items)
        return agg_res

    async def create_sale_order(self) -> SaleOrderModel:
        return await SaleOrderModel.create(
            id=self.sale_id, status=SaleOrderStatusType.DRAFT.value
        )

    async def create_sale_items(
        self, sale_order: SaleOrderModel
    ) -> List[SaleOrderItemModel]:
        items = [
            SaleOrderItemModel(
                id=uuid.uuid4(),
                sale_order=sale_order,
                #
                product_id=ele.product_id,
                sku=ele.sku,
                unique_identifier=ele.unique_identifier,
                #
                quantity=ele.quantity,
                price=ele.price,
            )
            for ele in self.sale_items
        ]
        sale_order_items = await SaleOrderItemModel.bulk_create(items)
        return sale_order_items

    @classmethod
    async def add_transaction(
        cls,
        sale_order: SaleOrderModel,
        sale_order_items: List[SaleOrderItemModel],
    ):
        stocks = [
            InventoryTransactionModel(
                id=uuid.uuid4(),
                #
                sku=ele.sku,
                product_id=ele.product_id,
                #
                quantity=~ele.quantity
                + 1,  # bitwise not operator to convert positive to negative
                transaction_type=TransactionType.SALE.value,
                #
                sale_order=sale_order,
            )
            for ele in sale_order_items
        ]
        await InventoryTransactionModel.bulk_create(stocks)

    @classmethod
    async def run_aggregation(
        cls, sale_order: SaleOrderModel, sale_items: List[SaleOrderItemModel]
    ):
        raw_sql = f"""
            SELECT sale_order_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
            FROM sale_order_item
            WHERE sale_order_id = $1
            GROUP BY sale_order_id
            """
        res_len, list_values = await Tortoise.get_connection(
            TORTOISE_DEFAULT_CONN_NAME
        ).execute_query(raw_sql, [sale_order.id])

        if res_len != 1:
            # filter by purchase id must return only one row for list_values
            raise Exception("Internal Error")

        total_price, total_units = (
            list_values[0]["total_price"],
            list_values[0]["total_units"],
        )
        sale_items = [SaleItemRes(**ele.__dict__) for ele in sale_items]

        return CreateSaleOrderRes(
            id=sale_order.id,
            created=sale_order.created,
            modified=sale_order.modified,
            total_price=total_price,
            total_units=total_units,
            sale_items=sale_items,
            status=sale_order.status,
        )


class AutoFillSaleOrder:
    def __init__(self, sale_id: int):
        self.sale_id = sale_id

    async def auto_fill(self):
        sale_order = await SaleOrderModel.get_or_none(id=self.sale_id)
        if not sale_order:
            raise Exception("Sale order not found")

        if sale_order.status != SaleOrderStatusType.DRAFT.value:
            raise Exception("Sale order is not in draft status")

        sale_order_items = await SaleOrderItemModel.filter(
            sale_order_id=self.sale_id
        )
        purchase_item_entity_selection = (
            await self.update_status_purchase_entities(sale_order_items)
        )
        await self.add_sale_order_entities(
            sale_order, purchase_item_entity_selection
        )
        sale_order.status = SaleOrderStatusType.CONFIRMED.value
        await sale_order.save(update_fields=["status"])
        return SaleOrderRes(**sale_order.__dict__)

    @classmethod
    async def update_status_purchase_entities(
        cls, sale_order_items: List[SaleOrderItemModel]
    ):
        future_tasks = []
        purchase_item_entity_selection = []
        for item in sale_order_items:
            queryset = PurchaseItemEntityModel.filter(
                product_id=item.product_id,
                sku=item.sku,
                status=EntityStockStatusType.AVAILABLE.value,
            ).limit(item.quantity)
            list_ids = await queryset.values_list("id", flat=True)
            if not list_ids:
                raise Exception("Not enough stock")

            purchase_item_entity_selection.append(
                {
                    "sale_order_item_id": item.id,
                    "purchase_item_entities": list_ids,
                }
            )

            # TODO: add unique_identifier selection from Inventory Management System
            # if item.unique_identifier:
            #     queryset = queryset.filter(unique_identifier=item.unique_identifier)

            future_tasks.append(
                PurchaseItemEntityModel.filter(id__in=list_ids).update(
                    status=EntityStockStatusType.SOLD.value
                )
            )

        await asyncio.gather(*future_tasks)
        return purchase_item_entity_selection

    @classmethod
    async def add_sale_order_entities(
        cls,
        new_sale_order: SaleOrderModel,
        purchase_item_entity_selection: List[dict],
    ):
        # add SaleOrderItemEntityModel
        list_sale_order_item_entities = []
        for sale_order_item in purchase_item_entity_selection:
            sale_order_item_id = sale_order_item["sale_order_item_id"]
            list_purchase_item_entity_ids = sale_order_item[
                "purchase_item_entities"
            ]
            list_being_created = [
                SaleOrderItemEntityModel(
                    id=uuid.uuid4(),
                    #
                    sale_order_id=new_sale_order.id,
                    sale_order_item_id=sale_order_item_id,
                    #
                    purchase_item_entity_id=purchase_item_entity_id,
                )
                for purchase_item_entity_id in list_purchase_item_entity_ids
            ]
            list_sale_order_item_entities.extend(list_being_created)
            if len(list_sale_order_item_entities) >= CHUNK_SIZE:
                await bulk_create_model(
                    SaleOrderItemEntityModel, list_sale_order_item_entities
                )

        await bulk_create_model(
            SaleOrderItemEntityModel, list_sale_order_item_entities
        )


class GetListSaleOrderService:
    def __init__(self, sale_order_ids: Union[List[int], None] = None):
        self.sale_order_ids = sale_order_ids if sale_order_ids else []

    async def get_list_sale_orders(
        self,
        limit: int,
        offset: int,
        status_filter: SaleOrderStatusType = None,
    ) -> GetListSaleOrderRes:
        _selected_fields = f"""
            sub_query.sale_order_id,
            sub_query.total_price,
            sub_query.total_units,
            sale_order.status,
            sale_order.created,
            sale_order.modified"""

        if status_filter:
            sale_order_ids = await SaleOrderModel.filter(
                status=status_filter.value
            ).values_list("id", flat=True)
            self.sale_order_ids.extend(sale_order_ids)

        if not self.sale_order_ids:
            queryset = SaleOrderModel.all()
            raw_sql = f"""
            SELECT %s
            FROM (
                SELECT sale_order_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
                FROM sale_order_item
                GROUP BY sale_order_id
                ORDER BY sale_order_id DESC
                LIMIT $1
                OFFSET $2) as sub_query
            INNER JOIN sale_order ON sub_query.sale_order_id = sale_order.id
            ORDER BY sub_query.sale_order_id DESC
            """
            params = [limit, offset]
        else:
            queryset = SaleOrderModel.filter(id__in=self.sale_order_ids)
            len_order_ids = len(self.sale_order_ids)

            where_clause = ", ".join(
                [f"${i + 1}" for i in range(len_order_ids)]
            )
            raw_sql = f"""
                SELECT %s
                FROM (
                    SELECT sale_order_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
                    FROM sale_order_item
                    WHERE sale_order_id IN ({where_clause})
                    GROUP BY sale_order_id
                    ORDER BY sale_order_id DESC
                    LIMIT ${len_order_ids + 1}
                    OFFSET ${len_order_ids + 2}) as sub_query
                INNER JOIN sale_order ON sub_query.sale_order_id = sale_order.id
                ORDER BY sub_query.sale_order_id DESC
                """
            params = [ele for ele in self.sale_order_ids] + [
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

        results: List[SaleOrderResV2] = []
        for sale_order in list_values:
            sale_order_res = SaleOrderResV2(
                id=sale_order.get("sale_order_id"),
                total_price=sale_order.get("total_price"),
                total_units=sale_order.get("total_units"),
                created=sale_order.get("created"),
                modified=sale_order.get("modified"),
                status=sale_order.get("status"),
            )
            results.append(sale_order_res)

        return GetListSaleOrderRes(results=results, total=total)
