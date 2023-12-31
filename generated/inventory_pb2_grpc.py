# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import inventory_pb2 as inventory__pb2


class InventoryServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetQuantity = channel.unary_unary(
                '/inventory.InventoryService/GetQuantity',
                request_serializer=inventory__pb2.GetQuantityReq.SerializeToString,
                response_deserializer=inventory__pb2.GetQuantityRes.FromString,
                )
        self.CreateSaleOrder = channel.unary_unary(
                '/inventory.InventoryService/CreateSaleOrder',
                request_serializer=inventory__pb2.CreateSaleOrderReq.SerializeToString,
                response_deserializer=inventory__pb2.SaleOrderRes.FromString,
                )
        self.GetSaleOrders = channel.unary_unary(
                '/inventory.InventoryService/GetSaleOrders',
                request_serializer=inventory__pb2.GetSaleOrdersReq.SerializeToString,
                response_deserializer=inventory__pb2.GetSaleOrdersRes.FromString,
                )


class InventoryServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetQuantity(self, request, context):
        """Get quantity by product ID or SKUs
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateSaleOrder(self, request, context):
        """Create a sale
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetSaleOrders(self, request, context):
        """Get sale orders
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_InventoryServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetQuantity': grpc.unary_unary_rpc_method_handler(
                    servicer.GetQuantity,
                    request_deserializer=inventory__pb2.GetQuantityReq.FromString,
                    response_serializer=inventory__pb2.GetQuantityRes.SerializeToString,
            ),
            'CreateSaleOrder': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateSaleOrder,
                    request_deserializer=inventory__pb2.CreateSaleOrderReq.FromString,
                    response_serializer=inventory__pb2.SaleOrderRes.SerializeToString,
            ),
            'GetSaleOrders': grpc.unary_unary_rpc_method_handler(
                    servicer.GetSaleOrders,
                    request_deserializer=inventory__pb2.GetSaleOrdersReq.FromString,
                    response_serializer=inventory__pb2.GetSaleOrdersRes.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'inventory.InventoryService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class InventoryService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetQuantity(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/GetQuantity',
            inventory__pb2.GetQuantityReq.SerializeToString,
            inventory__pb2.GetQuantityRes.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CreateSaleOrder(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/CreateSaleOrder',
            inventory__pb2.CreateSaleOrderReq.SerializeToString,
            inventory__pb2.SaleOrderRes.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetSaleOrders(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/GetSaleOrders',
            inventory__pb2.GetSaleOrdersReq.SerializeToString,
            inventory__pb2.GetSaleOrdersRes.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
