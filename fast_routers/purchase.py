from typing import List

import tortoise.transactions
from fastapi import APIRouter, HTTPException, status
from models import PurchaseModel
from services.logger import logger
from services.purchase import (
    CreatePurchaseItemRes,
    CreatePurchaseReq,
    CreatePurchaseRes,
    CreatePurchaseService,
    GetLatestPurchaseIdRes,
    GetListPurchaseRes,
    GetListPurchaseService,
    get_latest_purchase_id,
    list_purchase_items,
)
from tortoise.exceptions import IntegrityError


class PurchaseRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_routers()

    def _init_routers(self):
        self.add_api_route(
            "/",
            self._create_purchase,
            methods=["POST"],
        )
        self.add_api_route(
            "/",
            self._list_purchases,
            methods=["GET"],
        )
        self.add_api_route(
            "/{purchase_id}/items/",
            self._list_purchase_items,
            methods=["GET"],
        )
        self.add_api_route(
            "/latest-purchase-id/",
            self._get_latest_purchase_id,
            methods=["GET"],
        )

    @tortoise.transactions.atomic()
    async def _create_purchase(
        self, body: CreatePurchaseReq
    ) -> CreatePurchaseRes:
        handler = CreatePurchaseService(
            purchase_id=body.id, purchase_items=body.purchase_items
        )
        try:
            purchase = await handler.create_purchase()
            purchase_items = await handler.create_purchase_items(purchase)
            await handler.create_stock_transaction(purchase, purchase_items)
            await handler.create_purchase_item_entities(
                purchase, purchase_items
            )
            res = await handler.run_aggregation(
                purchase=purchase, purchase_items=purchase_items
            )
            return res
        except IntegrityError as e:
            logger.error(
                "[%s] create purchase %s failed, error: %s"
                % (self.__class__.__name__, body, e)
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase id already exists",
            )
        except Exception as e:
            logger.error(
                "[%s] create purchase %s failed, error: %s"
                % (self.__class__.__name__, body, e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="create purchase failed",
            )

    @classmethod
    async def _list_purchases(
        cls, limit: int = 10, offset: int = 0
    ) -> GetListPurchaseRes:
        handler = GetListPurchaseService()
        return await handler.get_list_purchases(limit=limit, offset=offset)

    @classmethod
    async def _list_purchase_items(
        cls, purchase_id: int
    ) -> List[CreatePurchaseItemRes]:
        purchase = await PurchaseModel.get_or_none(id=purchase_id)
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase id not found",
            )
        return await list_purchase_items(purchase=purchase)

    async def _get_latest_purchase_id(self) -> GetLatestPurchaseIdRes:
        logger.info("[%s] get latest purchase id" % self.__class__.__name__)
        return await get_latest_purchase_id()
