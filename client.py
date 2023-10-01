import os

import grpc
from dotenv import load_dotenv

from services.logger import logger
from generated import inventory_pb2, inventory_pb2_grpc

#
load_dotenv()


def client():
    with grpc.insecure_channel(
        os.environ.get("INVENTORY_SERVER_CHANNEL")
    ) as channel:
        logger.info("Connecting to inventory server...")
        logger.info(channel)
        inventory_stub = inventory_pb2_grpc.InventoryServiceStub(channel)

        choice = 1
        while choice > 0:
            instruction()
            try:
                choice = int(input("Enter choice: "))
                if choice == 1:
                    create_product(inventory_stub)
                elif choice == 2:
                    create_product_stock(inventory_stub)
                elif choice == 3:
                    add_stock_count(inventory_stub)
                elif choice == 4:
                    get_inventory_by_sku(inventory_stub)
                elif choice == 5:
                    get_list_product_stocks(inventory_stub)
                elif choice == 6:
                    get_inventory_by_product_id(inventory_stub)
                elif choice == 10:
                    break
                else:
                    print("Invalid choice")
            except Exception as e:
                print(e)
                choice = 0


def create_product(stub: inventory_pb2_grpc.InventoryServiceStub):
    logger.info("Calling CreateProduct...")
    product_id = input("Enter product id: ")
    logger.info("Request: %s", product_id)
    response = stub.CreateProduct(inventory_pb2.Product(id=product_id))
    logger.info(response)


def create_product_stock(stub: inventory_pb2_grpc.InventoryServiceStub):
    logger.info("Calling CreateProductStock...")
    product_id = input("Enter product id: ")
    sku = input("Enter sku: ")
    logger.info("Request: %s", product_id)
    response = stub.CreateProductStock(
        inventory_pb2.CreateProductStockRequest(product_id=product_id, sku=sku)
    )
    logger.info(response)


def add_stock_count(stub: inventory_pb2_grpc.InventoryServiceStub):
    logger.info("Calling AddStockCount...")
    sku = input("Enter sku: ")
    quantity = input("Enter quantity: ")
    logger.info("Request: %s", sku)
    response = stub.AddStockCount(
        inventory_pb2.AddStockGivenSkuRequest(sku=sku, quantity=int(quantity))
    )
    logger.info(response)


def get_inventory_by_sku(stub: inventory_pb2_grpc.InventoryServiceStub):
    logger.info("Calling GetInventoryBySku...")
    sku = input("Enter sku: ")
    logger.info("Request: %s", sku)
    response = stub.GetInventoryBySku(
        inventory_pb2.GetInventoryBySkuRequest(sku=sku)
    )
    logger.info(response)


def get_inventory_by_product_id(stub: inventory_pb2_grpc.InventoryServiceStub):
    logger.info("Calling GetInventoryByProductId...")
    # product_id = input("Enter product id: ")
    product_id = "7bedecb8-4da9-4026-8955-40787787bac9"
    logger.info("Request: %s", product_id)
    response = stub.GetInventoryByProductId(
        inventory_pb2.GetInventoryByProductIdRequest(product_id=product_id)
    )
    print("check response")
    print(response)


def get_list_product_stocks(stub: inventory_pb2_grpc.InventoryServiceStub):
    logger.info("Calling ListProductStocks...")
    # product_id = input("Enter product id: ")
    product_id = "7BEDECB8-4DA9-4026-8955-40787787BAC9"
    logger.info("Request: %s", product_id)
    response_iterator = stub.ListProductStocks(
        inventory_pb2.Product(id=product_id)
    )
    for response in response_iterator:
        logger.info(response)


def instruction():
    print("1. Create Product")
    print("2. Create Product Stock")
    print("3. Add Stock Count")
    print("4. Get Inventory by SKU")
    print("5. Get List Product Stocks")
    print("6. Get Inventory by Product ID")
    print("10. Exit")


# GetInventoryByProductId

if __name__ == "__main__":
    client()
