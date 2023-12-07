import tortoise.transactions  # noqa
from fastapi import APIRouter
from models import SaleOrderStatusType
from services.sale_order import (
    AutoFillSaleOrder,
    GetListSaleOrderRes,
    GetListSaleOrderService,
    SaleOrderRes,
)


class SaleOrderRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_routers()

    def _init_routers(self):
        self.add_api_route(
            "/",
            self._get_list_sale_orders,
            methods=["GET"],
        )
        self.add_api_route(
            "/{sale_id}/auto-fill/",
            self._auto_fill_sale_order,
            methods=["POST"],
        )

    @tortoise.transactions.atomic()
    async def _auto_fill_sale_order(self, sale_id: int) -> SaleOrderRes:
        handler = AutoFillSaleOrder(sale_id=sale_id)
        return await handler.auto_fill()

    @classmethod
    async def _get_list_sale_orders(
        cls,
        limit: int = 10,
        offset: int = 0,
        status_filter: SaleOrderStatusType = None,
    ) -> GetListSaleOrderRes:
        handler = GetListSaleOrderService()
        return await handler.get_list_sale_orders(limit, offset, status_filter)
