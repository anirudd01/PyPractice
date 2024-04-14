import grpc
import customer_pb2
import customer_pb2_grpc

class CustomerClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = customer_pb2_grpc.CustomerServiceStub(self.channel)

    def create_customer(self, name, email):
        request = customer_pb2.CustomerRequest(name=name, email=email)
        response = self.stub.CreateCustomer(request)
        return response.id

    def get_customer(self, customer_id):
        request = customer_pb2.CustomerRequest(id=customer_id)
        response = self.stub.GetCustomer(request)
        return {'id': response.id, 'name': response.name, 'email': response.email}

    def update_customer(self, customer_id, name, email):
        request = customer_pb2.CustomerRequest(id=customer_id, name=name, email=email)
        response = self.stub.UpdateCustomer(request)
        return response.id

    def delete_customer(self, customer_id):
        request = customer_pb2.CustomerRequest(id=customer_id)
        response = self.stub.DeleteCustomer(request)
        return response.id