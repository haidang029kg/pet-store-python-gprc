import grpc
import tortoise.transactions
from generated import inventory_pb2, inventory_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from models import SaleOrderStatusType
from services.logger import logger
from services.quantity import get_quantity
from services.sale_order import (
    CreateSaleOrderReq,
    CreateSaleOrderService,
    GetListSaleOrderService,
    SaleItemReq,
)
from tortoise.exceptions import IntegrityError


class InventoryRpcServicer(inventory_pb2_grpc.InventoryServiceServicer):
    async def GetQuantity(self, request, context):
        logger.info(
            "[%s] GetQuantity: %s" % (self.__class__.__name__, request)
        )

        if not request.skus and not request.product_id:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(
                "request.skus and request.product_id are empty"
            )
            return inventory_pb2.GetQuantityRes()

        res = await get_quantity(
            product_id=request.product_id, skus=request.skus
        )
        results = [
            inventory_pb2.QuantityBySku(
                product_id=str(ele.product_id),
                sku=ele.sku,
                quantity=ele.quantity,
            )
            for ele in res.results
        ]
        return inventory_pb2.GetQuantityRes(results=results)

    @tortoise.transactions.atomic()
    async def CreateSaleOrder(
        self, request: inventory_pb2.CreateSaleOrderReq, context
    ):
        logger.info(
            "[%s] CreateSaleOrder: %s" % (self.__class__.__name__, request)
        )

        if request.items is None or len(request.items) == 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("request.items is empty")
            return inventory_pb2.SaleOrderRes()

        data = CreateSaleOrderReq(
            id=request.id,
            sale_items=[
                SaleItemReq(
                    product_id=ele.product_id,
                    sku=ele.sku,
                    quantity=ele.quantity,
                    price=ele.price,
                    unique_identifier=ele.unique_identifier,
                )
                for ele in request.items
            ],
        )
        handler = CreateSaleOrderService(data=data)
        try:
            res = await handler.create()
        except IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("Sale order id already exists")
            return inventory_pb2.SaleOrderRes()

        gg_created, gg_modified = Timestamp(), Timestamp()
        (
            gg_created.FromDatetime(res.created),
            gg_modified.FromDatetime(res.modified),
        )
        return inventory_pb2.SaleOrderRes(
            created=gg_created,
            modified=gg_modified,
            total_price=res.total_price,
            total_units=res.total_units,
            items=[
                inventory_pb2.SaleOrderItem(
                    product_id=str(ele.product_id),
                    sku=ele.sku,
                    quantity=ele.quantity,
                    price=ele.price,
                )
                for ele in res.sale_items
            ],
            id=res.id,
            status=res.status.value,
        )

    async def GetSaleOrders(
        self, request: inventory_pb2.GetSaleOrdersReq, context
    ):
        logger.info(
            "[%s] GetSaleOrders: %s" % (self.__class__.__name__, request)
        )

        _limit = request.limit or 10
        _offset = request.offset or 0
        _status_filter = request.status or None

        if _status_filter:
            # convert to SaleOrderStatusType from proto enum
            _status_filter = (
                inventory_pb2._SALEORDERSTATUS.values_by_number.get(
                    _status_filter
                )
            )  # noqa
            _status_filter = SaleOrderStatusType[_status_filter.name]

        handler = GetListSaleOrderService()
        res = await handler.get_list_sale_orders(
            limit=_limit, offset=_offset, status_filter=_status_filter
        )
        results = []
        for sale_order in res.results:
            gg_created, gg_modified = Timestamp(), Timestamp()
            (
                gg_created.FromDatetime(sale_order.created),
                gg_modified.FromDatetime(sale_order.modified),
            )
            sale_order_res = inventory_pb2.SaleOrderSummary(
                id=sale_order.id,
                status=sale_order.status.value,
                total_price=sale_order.total_price,
                total_units=sale_order.total_units,
                created=gg_created,
                modified=gg_modified,
            )
            results.append(sale_order_res)

        return inventory_pb2.GetSaleOrdersRes(results=results, total=res.total)
