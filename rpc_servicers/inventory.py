import uuid

import grpc
from tortoise.functions import Sum

from models import (
    ProductModel,
    StockModel,
    StockTransactionModel,
    TransactionType,
)
from services.logger import logger
from generated import inventory_pb2, inventory_pb2_grpc


class InventoryServicer(inventory_pb2_grpc.InventoryServiceServicer):
    async def CreateProduct(
        self, request: inventory_pb2.CreateProductRequest, context
    ):
        logger.info("CreateProduct: %s", request)
        new_product = await ProductModel.create(id=request.id)
        return inventory_pb2.Product(id=str(new_product.id))

    async def CreateProductStock(
        self, request: inventory_pb2.CreateProductStockRequest, context
    ):
        logger.info("CreateProductStock: %s", request)
        # validate product id
        product = await ProductModel.get(id=request.product_id)
        if not product:
            context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")

        stock = await StockModel.create(sku=request.sku, product_id=product.id)
        return inventory_pb2.ProductStock(
            product_id=str(stock.product.id), sku=stock.sku
        )

    async def ListProductStocks(
        self,
        request: inventory_pb2.ProductIdRequest,
        context,
    ):
        logger.info("ListProductStocks: %s", request)
        # validate product id
        product = await ProductModel.get_or_none(id=request.product_id)
        if not product:
            context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")

        stocks = await StockModel.filter(product_id=product.id).select_related("product")
        for ele in stocks:
            reply = inventory_pb2.ProductStock(
                product_id=str(ele.product_id),
                sku=ele.sku,
                created=int(ele.created.timestamp()),
                modified=int(ele.modified.timestamp()),
            )
            yield reply

    async def AddStockCount(
        self, request: inventory_pb2.AddStockGivenSkuRequest, context
    ):
        logger.info("AddStockCount: %s", request)
        # validate sku
        stock = await StockModel.get_or_none(sku=request.sku)
        if not stock:
            context.abort(grpc.StatusCode.NOT_FOUND, "Stock not found")
        if request.quantity < 1:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid quantity")

        stock_transaction = await StockTransactionModel.create(
            id=uuid.uuid4(),
            stock_id=stock.sku,
            quantity=request.quantity,
            transaction_type=TransactionType.PURCHASE.value,
        )

        return inventory_pb2.StockCountTransaction(
            sku=stock.sku,
            quantity=stock_transaction.quantity,
            type=stock_transaction.transaction_type.value,
        )

    async def GetInventoryBySku(
        self, request: inventory_pb2.GetInventoryBySkuRequest, context
    ):
        logger.info("GetInventoryBySku: %s", request)
        # validate sku
        stock = await StockModel.get_or_none(sku=request.sku)
        if not stock:
            context.abort(grpc.StatusCode.NOT_FOUND, "Stock not found")
        # sum total quantity of stock transaction in db
        stock_transactions = (
            await StockTransactionModel.filter(stock=stock)
            .annotate(total_quantity=Sum("quantity"))
            .group_by("stock_id")
            .values("total_quantity")
        )
        return inventory_pb2.Inventory(
            sku=stock.sku, quantity=stock_transactions[0]["total_quantity"]
        )

    async def GetInventoryByProductId(
        self, request: inventory_pb2.GetInventoryByProductIdRequest, context
    ):
        logger.info("GetInventoryByProductId: %s", request)
        # validate product id
        product = await ProductModel.get_or_none(id=request.product_id)
        if not product:
            context.abort(grpc.StatusCode.NOT_FOUND, "Product not found")
        list_sku = await StockModel.filter(product=product).values_list(
            "sku", flat=True
        )

        stock_transactions = (
            await StockTransactionModel.filter(stock_id__in=list_sku)
            .annotate(total_quantity=Sum("quantity"))
            .group_by("stock_id")
            .values("stock_id", "total_quantity")
        )
        res = inventory_pb2.ListInventoryResponse()
        total_quantity = 0
        for ele in stock_transactions:
            res.inventory_by_sku.append(
                inventory_pb2.Inventory(
                    sku=ele["stock_id"], quantity=ele["total_quantity"]
                )
            )
            total_quantity += ele["total_quantity"]

        res.total_quantity = total_quantity
        return res
