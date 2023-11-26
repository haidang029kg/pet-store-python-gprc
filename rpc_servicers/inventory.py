import asyncio
import uuid
from typing import List, Type, Union

import grpc
import tortoise.transactions
from generated import inventory_pb2, inventory_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from models import (
    EntityStockStatusType,
    InventoryTransactionModel,
    PurchaseItemEntityModel,
    PurchaseItemModel,
    PurchaseModel,
    SaleOrderItemEntityModel,
    SaleOrderItemModel,
    SaleOrderModel,
    TransactionType,
)
from services import chunk_size_splitter, logger
from settings import CHUNK_SIZE, TORTOISE_DEFAULT_CONN_NAME
from tortoise import Tortoise
from tortoise.functions import Sum


class InventoryServicer(inventory_pb2_grpc.InventoryServiceServicer):
    @tortoise.transactions.atomic()
    async def CreatePurchase(
        self, request: inventory_pb2.CreatePurchaseReq, context
    ):
        """
        CreatePurchase is an asynchronous method that creates a purchase order in the inventory system.

        This method performs the following steps:
        - Creates a new purchase order
        - Creates purchase items associated with the order
        - Adds a quantity transaction for the purchase
        - Creates purchase item entities in the warehouse

        Args:
            request (inventory_pb2.CreatePurchaseReq): The request object containing the details of the purchase order.
            context: The context in which the request is being made.

        Raises:
            grpc.RpcError: If the request items are None or empty.

        Returns:
            inventory_pb2.PurchaseRes: The response object containing the details of the created purchase order.
        """

        logger.info("CreatePurchase: %s", request)
        if request.items is None or len(request.items) == 0:
            raise grpc.RpcError(
                grpc.StatusCode.INVALID_ARGUMENT, "request.items is empty"
            )

        # Create purchase
        new_purchase = await PurchaseModel.create(
            id=uuid.uuid4(), note=request.note, external_id=request.external_id
        )

        items = [
            PurchaseItemModel(
                id=uuid.uuid4(),
                product_id=ele.product_id,
                purchase=new_purchase,
                sku=ele.sku,
                quantity=ele.quantity,
                unique_identifier=ele.unique_identifier,
                price=ele.price,
            )
            for ele in request.items
        ]
        # Create purchase items
        purchase_items = await PurchaseItemModel.bulk_create(items)

        # add quantity transaction for this purchase
        stocks = [
            InventoryTransactionModel(
                id=uuid.uuid4(),
                sku=ele.sku,
                product_id=ele.product_id,
                unique_identifier=ele.unique_identifier,
                quantity=ele.quantity,
                transaction_type=TransactionType.PURCHASE.value,
                purchase=new_purchase,
            )
            for ele in purchase_items
        ]
        await InventoryTransactionModel.bulk_create(stocks)

        # add purchase item entity
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
                            unique_identifier=purchase_item.unique_identifier,
                            #
                            status=EntityStockStatusType.AVAILABLE.value,
                            #
                            purchase_id=new_purchase.id,
                            purchase_item_id=purchase_item.id,
                        )
                        for _ in range(chunk)
                    ]
                )
                if len(purchase_item_entities) >= CHUNK_SIZE:
                    await self._bulk_create_model(
                        PurchaseItemEntityModel,
                        purchase_item_entities,
                    )

        await self._bulk_create_model(
            PurchaseItemEntityModel, purchase_item_entities
        )

        # run aggregate query to get total price and total units
        raw_sql = f"""
            SELECT purchase_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
            FROM purchase_item
            WHERE purchase_id = $1
            GROUP BY purchase_id
            """
        res_len, list_values = await Tortoise.get_connection(
            TORTOISE_DEFAULT_CONN_NAME
        ).execute_query(raw_sql, [str(new_purchase.id)])
        if res_len != 1:
            # filter by purchase id must return only one row for list_values
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, "Internal error")

        total_price, total_units = (
            list_values[0]["total_price"],
            list_values[0]["total_units"],
        )
        gg_created, gg_modified = Timestamp(), Timestamp()
        (
            gg_created.FromDatetime(new_purchase.created),
            gg_modified.FromDatetime(new_purchase.modified),
        )

        return inventory_pb2.PurchaseRes(
            created=gg_created,
            modified=gg_modified,
            total_price=total_price,
            total_units=total_units,
            items=[
                inventory_pb2.PurchaseItem(
                    product_id=str(ele.product_id),
                    sku=ele.sku,
                    quantity=ele.quantity,
                    unique_identifier=ele.unique_identifier,
                    price=ele.price,
                )
                for ele in purchase_items
            ],
            external_id=new_purchase.external_id,
        )

    async def GetQuantity(self, request, context):
        """
        GetQuantity is an asynchronous method that calculates the total quantity of a product in the inventory
        system.

        This method performs the following steps:
        - Validates the request parameters
        - Filters the inventory transactions based on the provided SKUs or product ID
        - Runs an aggregate query to calculate the total quantity for each SKU or product ID

        Args:
            request: The request object containing the SKUs or product ID.
            context: The context in which the request is being made.

        Raises:
            grpc.RpcError: If the request SKUs and product ID are both empty or if no aggregate results are found.

        Returns:
            inventory_pb2.GetQuantityRes: The response object containing the total quantity for each SKU or product
            ID.
        """
        logger.info("GetQuantity: %s", request)
        # validate
        if not request.skus and not request.product_id:
            raise grpc.RpcError(
                grpc.StatusCode.INVALID_ARGUMENT,
                "request.skus and request.product_id are empty",
            )

        # filter
        if request.skus:
            queryset = InventoryTransactionModel.filter(sku__in=request.skus)
        else:
            queryset = InventoryTransactionModel.filter(
                product_id=request.product_id
            )

        # run aggregate query
        agg = (
            await queryset.annotate(total_quantity=Sum("quantity"))
            .group_by("product_id", "sku")
            .values("product_id", "sku", "total_quantity")
        )

        if not agg:
            return inventory_pb2.GetQuantityRes(results=[])

        results = [
            inventory_pb2.QuantityBySku(
                product_id=str(ele.get("product_id")),
                sku=ele.get("sku"),
                quantity=ele.get("total_quantity"),
            )
            for ele in agg
        ]
        return inventory_pb2.GetQuantityRes(results=results)

    @tortoise.transactions.atomic()
    async def CreateSaleOrder(self, request, context):
        """
        CreateSaleOrder is an asynchronous method that creates a sale order in the inventory system.

        This method performs the following steps:
        - Validates the request items
        - Creates a new sale order
        - Creates sale order items associated with the order
        - Adds a quantity transaction for the sale
        - Updates the status of the purchase item entities
        - Creates sale order item entities
        - Runs an aggregate query to get total price and total units

        Args:
            request: The request object containing the details of the sale order.
            context: The context in which the request is being made.

        Raises:
            grpc.RpcError: If the request items are None or empty.

        Returns:
            inventory_pb2.SaleOrderRes: The response object containing the details of the created sale order.
        """
        logger.info("CreateSaleOrder: %s", request)
        if request.items is None or len(request.items) == 0:
            raise grpc.RpcError(
                grpc.StatusCode.INVALID_ARGUMENT, "request.items is empty"
            )
        # add sale order and sale order items
        new_sale_order = await SaleOrderModel.create(
            id=uuid.uuid4(), note=request.note
        )
        items = [
            SaleOrderItemModel(
                id=uuid.uuid4(),
                sale_order=new_sale_order,
                #
                product_id=ele.product_id,
                sku=ele.sku,
                unique_identifier=ele.unique_identifier,
                #
                quantity=ele.quantity,
                price=ele.price,
            )
            for ele in request.items
        ]
        sale_order_items = await SaleOrderItemModel.bulk_create(items)

        # add sale order transaction
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
                sale_order=new_sale_order,
            )
            for ele in sale_order_items
        ]
        await InventoryTransactionModel.bulk_create(stocks)

        # update purchase item entity status
        future_tasks = []
        purchase_item_entity_selection = []
        for item in sale_order_items:
            queryset = PurchaseItemEntityModel.filter(
                product_id=item.product_id,
                sku=item.sku,
                status=EntityStockStatusType.AVAILABLE.value,
            ).limit(item.quantity)
            list_ids = await queryset.values_list("id", flat=True)
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
                queryset.update(status=EntityStockStatusType.SOLD.value)
            )

        await asyncio.gather(*future_tasks)

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
                await self._bulk_create_model(
                    SaleOrderItemEntityModel, list_sale_order_item_entities
                )

        await self._bulk_create_model(
            SaleOrderItemEntityModel, list_sale_order_item_entities
        )

        raw_sql = f"""
            SELECT sale_order_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
            FROM sale_order_item
            WHERE sale_order_id = $1
            GROUP BY sale_order_id
            """
        res_len, list_values = await Tortoise.get_connection(
            TORTOISE_DEFAULT_CONN_NAME
        ).execute_query(raw_sql, [str(new_sale_order.id)])

        if res_len != 1:
            # filter by purchase id must return only one row for list_values
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, "Internal error")

        total_price, total_units = (
            list_values[0]["total_price"],
            list_values[0]["total_units"],
        )
        gg_created, gg_modified = Timestamp(), Timestamp()
        (
            gg_created.FromDatetime(new_sale_order.created),
            gg_modified.FromDatetime(new_sale_order.modified),
        )
        return inventory_pb2.SaleOrderRes(
            created=gg_created,
            modified=gg_modified,
            total_price=total_price,
            total_units=total_units,
            items=[
                inventory_pb2.SaleOrderItem(
                    product_id=str(ele.product_id),
                    sku=ele.sku,
                    quantity=ele.quantity,
                    price=ele.price,
                )
                for ele in sale_order_items
            ],
        )

    async def GetSaleOrders(self, request, context):
        """
        This method performs the following steps:
        - Validates the request parameters
        - Constructs a raw SQL query based on the request parameters
        - Executes the raw SQL query to retrieve the sale orders
        - Constructs the response object with the retrieved sale orders

        Args:
            request: The request object containing the order IDs.
            context: The context in which the request is being made.

        Returns:
            inventory_pb2.GetSaleOrdersRes: The response object containing the retrieved sale orders.
        """

        logger.info("GetSaleOrders: %s", request)
        _limit = request.limit or 10
        _offset = request.offset or 0

        _selected_fields = f"""
            sub_query.sale_order_id,
            sub_query.total_price,
            sub_query.total_units,
            sale_order.note,
            sale_order.created,
            sale_order.modified"""

        if not request.order_ids:
            queryset = SaleOrderModel.all()
            raw_sql = f"""
            SELECT %s
            FROM (
                SELECT sale_order_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
                FROM sale_order_item
                GROUP BY sale_order_id
                LIMIT $1
                OFFSET $2) as sub_query
            INNER JOIN sale_order ON sub_query.sale_order_id = sale_order.id
            """
            params = [_limit, _offset]
        else:
            queryset = SaleOrderModel.filter(id__in=request.order_ids)
            len_order_ids = len(request.order_ids)

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
                    LIMIT ${len_order_ids + 1}
                    OFFSET ${len_order_ids + 2}) as sub_query
                INNER JOIN sale_order ON sub_query.sale_order_id = sale_order.id
                """
            params = [str(ele) for ele in request.order_ids] + [
                _limit,
                _offset,
            ]

        total_promise = queryset.count()
        sql_promise = Tortoise.get_connection(
            TORTOISE_DEFAULT_CONN_NAME
        ).execute_query(raw_sql % _selected_fields, params)
        total, (res_len, list_values) = await asyncio.gather(
            total_promise, sql_promise
        )

        results = []
        for sale_order in list_values:
            gg_created, gg_modified = Timestamp(), Timestamp()
            (
                gg_created.FromDatetime(sale_order.get("created")),
                gg_modified.FromDatetime(sale_order.get("modified")),
            )
            sale_order_res = inventory_pb2.SaleOrderSummary(
                id=str(sale_order.get("sale_order_id")),
                note=sale_order.get("note"),
                total_price=sale_order.get("total_price"),
                total_units=sale_order.get("total_units"),
                created=gg_created,
                modified=gg_modified,
            )
            results.append(sale_order_res)

        return inventory_pb2.GetSaleOrdersRes(orders=results, total=total)

    @classmethod
    async def _bulk_create_model(
        cls,
        model: Union[
            Type[PurchaseItemEntityModel], Type[SaleOrderItemEntityModel]
        ],
        items: List[Union[PurchaseItemEntityModel, SaleOrderItemEntityModel]],
    ):
        """
        _bulk_create_model is an asynchronous class method that performs a bulk creation of model instances in the
        database.

        This method is a utility function that can be used to create multiple instances of a model in a single
        database operation,
        which can be more efficient than creating each instance individually.

        Args:
            model (Union[Type[PurchaseItemEntityModel], Type[SaleOrderItemEntityModel]]): The model class that
        instances are to be created for.
            items (List[Union[PurchaseItemEntityModel, SaleOrderItemEntityModel]]): A list of instances of the
        model that are to be created in the database.

        This method uses the `bulk_create` method of the model class to create the instances in the database.
        This is an asynchronous operation, as indicated by the `await` keyword, which means it's non-blocking and
        allows other tasks to run concurrently while waiting for the database operation to complete.
        """
        if items:
            await model.bulk_create(items)
            items.clear()
