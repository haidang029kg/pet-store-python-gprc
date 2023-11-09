import asyncio
import uuid

import grpc
import tortoise.transactions
from google.protobuf.timestamp_pb2 import Timestamp
from tortoise import Tortoise
from tortoise.functions import Sum

from generated import inventory_pb2, inventory_pb2_grpc
from models import (
    PurchaseModel,
    PurchaseItemModel,
    TransactionType, InventoryTransactionModel, PurchaseItemEntityModel, EntityStockStatusType, SaleOrderModel,
    SaleOrderItemModel, SaleOrderItemEntityModel,
)
from services import chunk_size_splitter, logger
from settings import TORTOISE_DEFAULT_CONN_NAME, CHUNK_SIZE


class InventoryServicer(inventory_pb2_grpc.InventoryServiceServicer):
    @tortoise.transactions.atomic()
    async def CreatePurchase(self, request: inventory_pb2.CreatePurchaseReq, context):
        logger.info("CreatePurchase: %s", request)
        if request.items is None or len(request.items) == 0:
            raise grpc.RpcError(grpc.StatusCode.INVALID_ARGUMENT, "request.items is empty")

        # Create a new purchase
        new_purchase = await PurchaseModel.create(id=uuid.uuid4(), note=request.note)
        items = [PurchaseItemModel(
            id=uuid.uuid4(),
            product_id=ele.product_id,
            purchase=new_purchase,
            sku=ele.sku,
            quantity=ele.quantity,
            unique_identifier=ele.unique_identifier,
            price=ele.price,
        ) for ele in request.items]
        # Create purchase items
        purchase_items = await PurchaseItemModel.bulk_create(items)

        raw_sql = f"""
            SELECT purchase_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
            FROM purchase_item
            WHERE purchase_id = $1
            GROUP BY purchase_id
        """
        res_len, list_values = await Tortoise.get_connection(TORTOISE_DEFAULT_CONN_NAME).execute_query(raw_sql, [
            str(new_purchase.id)])
        if res_len != 1:
            # filter by purchase id must return only one row for list_values
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, "Internal error")

        total_price, total_units = list_values[0]["total_price"], list_values[0]["total_units"]
        gg_created, gg_modified = Timestamp(), Timestamp()
        (gg_created.FromDatetime(new_purchase.created), gg_modified.FromDatetime(new_purchase.modified))

        # add quantity transaction for this purchase
        # TODO: add task to celery
        stocks = [InventoryTransactionModel(
            id=uuid.uuid4(),
            sku=ele.sku,
            product_id=ele.product_id,
            unique_identifier=ele.unique_identifier,
            quantity=ele.quantity,
            transaction_type=TransactionType.PURCHASE.value,
            purchase=new_purchase,
        ) for ele in purchase_items]
        await InventoryTransactionModel.bulk_create(stocks)

        # add entity stock for this purchase
        # TODO: add task to celery
        purchase_item_entities = []
        for purchase_item in purchase_items:
            chunks = chunk_size_splitter(CHUNK_SIZE, purchase_item.quantity)
            for chunk in chunks:
                purchase_item_entities.extend([
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
                    ) for _ in range(chunk)])
                if len(purchase_item_entities) > CHUNK_SIZE:
                    await PurchaseItemEntityModel.bulk_create(purchase_item_entities)
                    purchase_item_entities.clear()

        if purchase_item_entities:
            await PurchaseItemEntityModel.bulk_create(purchase_item_entities)

        return inventory_pb2.PurchaseRes(
            created=gg_created,
            modified=gg_modified,
            total_price=total_price,
            total_units=total_units,
            items=[inventory_pb2.PurchaseItem(
                product_id=str(ele.product_id),
                sku=ele.sku,
                quantity=ele.quantity,
                unique_identifier=ele.unique_identifier,
                price=ele.price,
            ) for ele in purchase_items],
        )

    async def GetQuantity(self, request, context):
        logger.info("GetQuantity: %s", request)
        # validate
        if not request.skus and not request.product_id:
            raise grpc.RpcError(grpc.StatusCode.INVALID_ARGUMENT, "request.skus and request.product_id are empty")

        if request.skus:
            queryset = InventoryTransactionModel.filter(sku__in=request.skus)
        else:
            queryset = InventoryTransactionModel.filter(product_id=request.product_id)

        agg = await queryset.annotate(total_quantity=Sum("quantity")).group_by("product_id", "sku").values(
            "product_id", "sku", "total_quantity")

        if not agg:
            raise grpc.RpcError(grpc.StatusCode.NOT_FOUND, "Not found")

        results = [
            inventory_pb2.QuantityBySku(
                product_id=str(ele.get("product_id")),
                sku=ele.get("sku"),
                quantity=ele.get("total_quantity"), )
            for ele in agg
        ]
        return inventory_pb2.GetQuantityRes(results=results)

    @tortoise.transactions.atomic()
    async def CreateSaleOrder(self, request, context):
        logger.info("CreateSaleOrder: %s", request)
        if request.items is None or len(request.items) == 0:
            raise grpc.RpcError(grpc.StatusCode.INVALID_ARGUMENT, "request.items is empty")
        # add sale order and sale order items
        new_sale_order = await SaleOrderModel.create(id=uuid.uuid4(), note=request.note)
        items = [SaleOrderItemModel(
            id=uuid.uuid4(),
            sale_order=new_sale_order,
            #
            product_id=ele.product_id,
            sku=ele.sku,
            unique_identifier=ele.unique_identifier,
            #
            quantity=ele.quantity,
            price=ele.price,
        ) for ele in request.items]
        sale_order_items = await SaleOrderItemModel.bulk_create(items)

        # add sale order transaction
        stocks = [InventoryTransactionModel(
            id=uuid.uuid4(),
            #
            sku=ele.sku,
            product_id=ele.product_id,
            #
            quantity=ele.quantity * -1,
            transaction_type=TransactionType.SALE.value,
            #
            sale_order=new_sale_order,
        ) for ele in sale_order_items]
        await InventoryTransactionModel.bulk_create(stocks)

        # update purchase item entity status
        gather_tasks = []
        tmp_ids = []
        for item in sale_order_items:
            queryset = PurchaseItemEntityModel.filter(
                product_id=item.product_id,
                sku=item.sku,
                status=EntityStockStatusType.AVAILABLE.value,
            ).limit(item.quantity)
            __tmp_ids = await queryset.values_list("id", flat=True)
            tmp_ids.extend(__tmp_ids)
            # TODO: add unique_identifier selection from Inventory Management System
            # if item.unique_identifier:
            #     queryset = queryset.filter(unique_identifier=item.unique_identifier)

            gather_tasks.append(queryset.update(status=EntityStockStatusType.SOLD.value))

        await asyncio.gather(*gather_tasks)

        # add  SaleOrderItemEntityModel
        sale_order_item_entities = []
        for sale_order_item in sale_order_items:
            queryset = PurchaseItemEntityModel.filter(
                product_id=sale_order_item.product_id,
                sku=sale_order_item.sku,
                status=EntityStockStatusType.SOLD.value,
            )

        raw_sql = f"""
            SELECT sale_order_id, SUM(price * quantity) as total_price, SUM(quantity) as total_units
            FROM sale_order_item
            WHERE sale_order_id = $1
            GROUP BY sale_order_id
        """
        res_len, list_values = await Tortoise.get_connection(TORTOISE_DEFAULT_CONN_NAME).execute_query(raw_sql, [
            str(new_sale_order.id)])

        if res_len != 1:
            # filter by purchase id must return only one row for list_values
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, "Internal error")

        total_price, total_units = list_values[0]["total_price"], list_values[0]["total_units"]
        gg_created, gg_modified = Timestamp(), Timestamp()
        (gg_created.FromDatetime(new_sale_order.created), gg_modified.FromDatetime(new_sale_order.modified))
        return inventory_pb2.SaleOrderRes(
            created=gg_created,
            modified=gg_modified,
            total_price=total_price,
            total_units=total_units,
            items=[inventory_pb2.SaleOrderItem(
                product_id=str(ele.product_id),
                sku=ele.sku,
                quantity=ele.quantity,
                price=ele.price,
            ) for ele in sale_order_items],
        )

        # async def CreateProduct(
        #         self, request: inventory_pb2.CreateProductRequest, context
        # ):
        #     logger.info("CreateProduct: %s", request)
        #     new_product = await ProductModel.create(id=request.id)
        #     return inventory_pb2.Product(id=str(new_product.id))
        #
        # async def CreateProductStock(
        #         self, request: inventory_pb2.CreateProductStockRequest, context
        # ):
        #     logger.info("CreateProductStock: %s", request)
        #     # validate product id
        #     product = await ProductModel.get(id=request.product_id)
        #     if not product:
        #         context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
        #
        #     stock = await StockModel.create(sku=request.sku, product_id=product.id)
        #     return inventory_pb2.ProductStock(
        #         product_id=str(stock.product.id), sku=stock.sku
        #     )
        #
        # async def ListProductStocks(
        #         self,
        #         request: inventory_pb2.ProductIdRequest,
        #         context,
        # ):
        #     logger.info("ListProductStocks: %s", request)
        #     # validate product id
        #     product = await ProductModel.get_or_none(id=request.product_id)
        #     if not product:
        #         context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
        #
        #     stocks = await StockModel.filter(product_id=product.id).select_related("product")
        #     for ele in stocks:
        #         reply = inventory_pb2.ProductStock(
        #             product_id=str(ele.product_id),
        #             sku=ele.sku,
        #             created=int(ele.created.timestamp()),
        #             modified=int(ele.modified.timestamp()),
        #         )
        #         yield reply
        #
        # async def AddStockCount(
        #         self, request: inventory_pb2.AddStockGivenSkuRequest, context
        # ):
        #     logger.info("AddStockCount: %s", request)
        #     # validate sku
        #     stock = await StockModel.get_or_none(sku=request.sku)
        #     if not stock:
        #         context.abort(grpc.StatusCode.NOT_FOUND, "Stock not found")
        #     if request.quantity < 1:
        #         context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid quantity")
        #
        #     stock_transaction = await StockTransactionModel.create(
        #         id=uuid.uuid4(),
        #         stock_id=stock.sku,
        #         quantity=request.quantity,
        #         transaction_type=TransactionType.PURCHASE.value,
        #     )
        #
        #     return inventory_pb2.StockCountTransaction(
        #         sku=stock.sku,
        #         quantity=stock_transaction.quantity,
        #         type=stock_transaction.transaction_type.value,
        #     )
        #
        # async def GetInventoryBySku(
        #         self, request: inventory_pb2.GetInventoryBySkuRequest, context
        # ):
        #     logger.info("GetInventoryBySku: %s", request)
        #     # validate sku
        #     stock = await StockModel.get_or_none(sku=request.sku)
        #     if not stock:
        #         context.abort(grpc.StatusCode.NOT_FOUND, "Stock not found")
        #     # sum total quantity of stock transaction in db
        #     stock_transactions = (
        #         await StockTransactionModel.filter(stock=stock)
        #         .annotate(total_quantity=Sum("quantity"))
        #         .group_by("stock_id")
        #         .values("total_quantity")
        #     )
        #     if not stock_transactions:
        #         return inventory_pb2.Inventory(sku=stock.sku, quantity=0)
        #     return inventory_pb2.Inventory(
        #         sku=stock.sku, quantity=stock_transactions[0]["total_quantity"]
        #     )
        #
        # async def GetInventoryByProductId(
        #         self, request: inventory_pb2.GetInventoryByProductIdRequest, context
        # ):
        #     logger.info("GetInventoryByProductId: %s", request)
        #     # validate product id
        #     product = await ProductModel.get_or_none(id=request.product_id)
        #     if not product:
        #         context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
        #     list_sku = await StockModel.filter(product=product).values_list(
        #         "sku", flat=True
        #     )
        #
        #     stock_transactions = (
        #         await StockTransactionModel.filter(stock_id__in=list_sku)
        #         .annotate(total_quantity=Sum("quantity"))
        #         .group_by("stock_id")
        #         .values("stock_id", "total_quantity")
        #     )
        #     res = inventory_pb2.ListInventoryResponse()
        #     total_quantity = 0
        #     for ele in stock_transactions:
        #         res.inventory_by_sku.append(
        #             inventory_pb2.Inventory(
        #                 sku=ele["stock_id"], quantity=ele["total_quantity"]
        #             )
        #         )
        #         total_quantity += ele["total_quantity"]
        #
        #     res.total_quantity = total_quantity
        #     return res
