from fastapi import FastAPI
from pp_grpc.client import CustomerClient
from pydantic import BaseModel
from typing import Optional
import grpc
import customer_pb2
import customer_pb2_grpc

app = FastAPI()

class Customer(BaseModel):
    name: str
    email: str
    id: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

customer_client = CustomerClient()

@app.post("/customers/", response_model=Customer)
async def create_customer(customer: Customer):
    customer_id = customer_client.create_customer(customer.name, customer.email)
    return {'id': customer_id, 'name': customer.name, 'email': customer.email}

@app.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = customer_client.get_customer(customer_id)
    return customer

@app.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    customer = customer_client.update_customer(customer_id, customer_update.name, customer_update.email)
    return {'id': customer_id, 'name': customer.name, 'email': customer.email}

@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    customer_client.delete_customer(customer_id)
    return {'message': 'Customer deleted'}