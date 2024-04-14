from concurrent import futures
import grpc
import customer_pb2
import customer_pb2_grpc
from pymongo import MongoClient

class CustomerService(customer_pb2_grpc.CustomerServiceServicer):
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['customer_db']
        self.customers = self.db['customers']

    def CreateCustomer(self, request, context):
        customer_id = self.customers.insert_one({
            'name': request.name,
            'email': request.email
        }).inserted_id
        return customer_pb2.CustomerResponse(id=str(customer_id))

    def GetCustomer(self, request, context):
        customer = self.customers.find_one({'_id': ObjectId(request.id)})
        if customer is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Customer not found')
            return customer_pb2.CustomerResponse()
        return customer_pb2.CustomerResponse(id=str(customer['_id']), name=customer['name'], email=customer['email'])

    def UpdateCustomer(self, request, context):
        customer = self.customers.find_one({'_id': ObjectId(request.id)})
        if customer is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Customer not found')
            return customer_pb2.CustomerResponse()
        self.customers.update_one({'_id': ObjectId(request.id)}, {'$set': {'name': request.name, 'email': request.email}})
        return customer_pb2.CustomerResponse(id=request.id)

    def DeleteCustomer(self, request, context):
        customer = self.customers.find_one({'_id': ObjectId(request.id)})
        if customer is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Customer not found')
            return customer_pb2.CustomerResponse()
        self.customers.delete_one({'_id': ObjectId(request.id)})
        return customer_pb2.CustomerResponse()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    customer_pb2_grpc.add_CustomerServiceServicer_to_server(CustomerService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()