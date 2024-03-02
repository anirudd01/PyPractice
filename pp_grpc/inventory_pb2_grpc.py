# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import inventory_pb2 as inventory__pb2


class InventoryServiceStub(object):
    """service def
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.AddProduct = channel.unary_unary(
                '/inventory.InventoryService/AddProduct',
                request_serializer=inventory__pb2.Product.SerializeToString,
                response_deserializer=inventory__pb2.InventoryResponse.FromString,
                )
        self.RemoveProduct = channel.unary_unary(
                '/inventory.InventoryService/RemoveProduct',
                request_serializer=inventory__pb2.InventoryReq.SerializeToString,
                response_deserializer=inventory__pb2.InventoryResponse.FromString,
                )
        self.UpdateProduct = channel.unary_unary(
                '/inventory.InventoryService/UpdateProduct',
                request_serializer=inventory__pb2.Product.SerializeToString,
                response_deserializer=inventory__pb2.InventoryResponse.FromString,
                )
        self.CheckInventory = channel.unary_unary(
                '/inventory.InventoryService/CheckInventory',
                request_serializer=inventory__pb2.InventoryReq.SerializeToString,
                response_deserializer=inventory__pb2.InventoryResponse.FromString,
                )
        self.ReserveProduct = channel.unary_unary(
                '/inventory.InventoryService/ReserveProduct',
                request_serializer=inventory__pb2.InventoryReq.SerializeToString,
                response_deserializer=inventory__pb2.InventoryResponse.FromString,
                )


class InventoryServiceServicer(object):
    """service def
    """

    def AddProduct(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveProduct(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateProduct(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CheckInventory(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReserveProduct(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_InventoryServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'AddProduct': grpc.unary_unary_rpc_method_handler(
                    servicer.AddProduct,
                    request_deserializer=inventory__pb2.Product.FromString,
                    response_serializer=inventory__pb2.InventoryResponse.SerializeToString,
            ),
            'RemoveProduct': grpc.unary_unary_rpc_method_handler(
                    servicer.RemoveProduct,
                    request_deserializer=inventory__pb2.InventoryReq.FromString,
                    response_serializer=inventory__pb2.InventoryResponse.SerializeToString,
            ),
            'UpdateProduct': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateProduct,
                    request_deserializer=inventory__pb2.Product.FromString,
                    response_serializer=inventory__pb2.InventoryResponse.SerializeToString,
            ),
            'CheckInventory': grpc.unary_unary_rpc_method_handler(
                    servicer.CheckInventory,
                    request_deserializer=inventory__pb2.InventoryReq.FromString,
                    response_serializer=inventory__pb2.InventoryResponse.SerializeToString,
            ),
            'ReserveProduct': grpc.unary_unary_rpc_method_handler(
                    servicer.ReserveProduct,
                    request_deserializer=inventory__pb2.InventoryReq.FromString,
                    response_serializer=inventory__pb2.InventoryResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'inventory.InventoryService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class InventoryService(object):
    """service def
    """

    @staticmethod
    def AddProduct(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/AddProduct',
            inventory__pb2.Product.SerializeToString,
            inventory__pb2.InventoryResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RemoveProduct(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/RemoveProduct',
            inventory__pb2.InventoryReq.SerializeToString,
            inventory__pb2.InventoryResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateProduct(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/UpdateProduct',
            inventory__pb2.Product.SerializeToString,
            inventory__pb2.InventoryResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CheckInventory(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/CheckInventory',
            inventory__pb2.InventoryReq.SerializeToString,
            inventory__pb2.InventoryResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ReserveProduct(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/inventory.InventoryService/ReserveProduct',
            inventory__pb2.InventoryReq.SerializeToString,
            inventory__pb2.InventoryResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)