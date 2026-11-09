"""gRPC server implementing all four RPC styles, plus a logging interceptor.

Run (inside pp_grpc/):  python server.py      -> listens on localhost:50051

Cheat sheet:
- Subclass the generated `<Service>Servicer` and override each RPC method.
- Unary method:            (self, request, context) -> response
- Server streaming:        (self, request, context) -> yield responses
- Client streaming:        (self, request_iterator, context) -> response
- Bidirectional streaming: (self, request_iterator, context) -> yield responses
- Errors: `context.abort(grpc.StatusCode.X, "msg")` raises and ends the call.
- Metadata (like HTTP headers): `context.invocation_metadata()`.
"""

import logging
import threading
import uuid
from concurrent import futures

import grpc
from google.protobuf import empty_pb2

import customer_pb2
import customer_pb2_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("grpc-server")


class CustomerService(customer_pb2_grpc.CustomerServiceServicer):
    """In-memory storage keeps the demo self-contained (swap for MongoDB/SQL in real code)."""

    def __init__(self) -> None:
        self._customers: dict[str, customer_pb2.Customer] = {}
        # The server handles calls on a thread pool, so guard shared state.
        self._lock = threading.Lock()

    # ---------- helpers ----------
    def _create(self, request: customer_pb2.CreateCustomerRequest, context) -> customer_pb2.Customer:
        if not request.name or not request.email:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "name and email are required")
        customer = customer_pb2.Customer(
            id=uuid.uuid4().hex[:8],
            name=request.name,
            email=request.email,
            tier=request.tier or customer_pb2.TIER_FREE,
            tags=list(request.tags),
        )
        customer.created_at.GetCurrentTime()  # Timestamp helper
        with self._lock:
            self._customers[customer.id] = customer
        return customer

    def _get_or_abort(self, customer_id: str, context) -> customer_pb2.Customer:
        customer = self._customers.get(customer_id)
        if customer is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"customer {customer_id} not found")
        return customer

    # ---------- 1) Unary ----------
    def CreateCustomer(self, request, context):
        return self._create(request, context)

    def GetCustomer(self, request, context):
        return self._get_or_abort(request.id, context)

    def UpdateCustomer(self, request, context):
        with self._lock:
            customer = self._get_or_abort(request.id, context)
            # HasField works because the fields are declared `optional` in the proto.
            if request.HasField("name"):
                customer.name = request.name
            if request.HasField("email"):
                customer.email = request.email
            if request.HasField("tier"):
                customer.tier = request.tier
            return customer

    def DeleteCustomer(self, request, context):
        with self._lock:
            self._get_or_abort(request.id, context)
            del self._customers[request.id]
        return empty_pb2.Empty()

    # ---------- 2) Server streaming ----------
    def ListCustomers(self, request, context):
        with self._lock:
            customers = list(self._customers.values())
        sent = 0
        for customer in customers:
            if not context.is_active():  # client cancelled or deadline passed
                return
            if request.tier and customer.tier != request.tier:
                continue
            yield customer
            sent += 1
            if request.page_size and sent >= request.page_size:
                return

    # ---------- 3) Client streaming ----------
    def BulkCreateCustomers(self, request_iterator, context):
        ids = [self._create(req, context).id for req in request_iterator]
        return customer_pb2.BulkCreateResponse(created_count=len(ids), ids=ids)

    # ---------- 4) Bidirectional streaming ----------
    def LookupCustomers(self, request_iterator, context):
        # Responses can be sent while requests are still arriving.
        for req in request_iterator:
            customer = self._customers.get(req.id)
            if customer is not None:
                yield customer
            else:
                logger.info("lookup: %s not found, skipping", req.id)


class LoggingInterceptor(grpc.ServerInterceptor):
    """Server interceptor = gRPC's version of middleware."""

    def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata or ())
        logger.info("call %s request-id=%s", handler_call_details.method, metadata.get("x-request-id", "-"))
        return continuation(handler_call_details)


def serve(port: int = 50051) -> grpc.Server:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[LoggingInterceptor()],
    )
    customer_pb2_grpc.add_CustomerServiceServicer_to_server(CustomerService(), server)
    # Insecure = no TLS. Production: server.add_secure_port(addr, grpc.ssl_server_credentials(...))
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("gRPC server listening on :%s", port)
    return server


if __name__ == "__main__":
    srv = serve()
    try:
        srv.wait_for_termination()
    except KeyboardInterrupt:
        srv.stop(grace=2).wait()  # let in-flight calls finish
