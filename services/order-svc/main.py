from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Order Service API",
    description="Microservice for managing orders",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]
    shipping_address: str

class Order(BaseModel):
    id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    status: str
    shipping_address: str
    created_at: str
    updated_at: Optional[str] = None

# In-memory storage (use database in production)
orders = [
    {
        "id": "order-1",
        "user_id": "1",
        "items": [
            {"product_id": "1", "quantity": 1, "price": 999.99},
            {"product_id": "4", "quantity": 2, "price": 149.99}
        ],
        "total_amount": 1299.97,
        "status": "completed",
        "shipping_address": "123 Main St, City, State",
        "created_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": "order-2",
        "user_id": "2",
        "items": [
            {"product_id": "2", "quantity": 1, "price": 699.99}
        ],
        "total_amount": 699.99,
        "status": "pending",
        "shipping_address": "456 Oak Ave, Town, State",
        "created_at": "2024-01-16T14:20:00Z"
    }
]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "order-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/orders", response_model=dict)
async def get_orders(user_id: Optional[str] = None, status: Optional[str] = None):
    filtered_orders = orders.copy()
    
    if user_id:
        filtered_orders = [o for o in filtered_orders if o['user_id'] == user_id]
    
    if status:
        filtered_orders = [o for o in filtered_orders if o['status'] == status]
    
    return {
        "service": "order-service",
        "data": filtered_orders,
        "count": len(filtered_orders),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/orders/{order_id}", response_model=dict)
async def get_order(order_id: str):
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "service": "order-service",
        "data": order
    }

@app.post("/orders", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate):
    # Calculate total amount
    total_amount = sum(item.quantity * item.price for item in order_data.items)
    
    new_order = {
        "id": f"order-{uuid.uuid4()}",
        "user_id": order_data.user_id,
        "items": [item.dict() for item in order_data.items],
        "total_amount": total_amount,
        "status": "pending",
        "shipping_address": order_data.shipping_address,
        "created_at": datetime.utcnow().isoformat()
    }
    
    orders.append(new_order)
    
    logger.info(f"Created new order: {new_order['id']}")
    
    return {
        "service": "order-service",
        "data": new_order
    }

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order['status'] = status
    order['updated_at'] = datetime.utcnow().isoformat()
    
    return {
        "service": "order-service",
        "data": order
    }

@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(order_id: str):
    global orders
    orders = [o for o in orders if o['id'] != order_id]
    return

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting Order Service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("DEVELOPMENT", "false").lower() == "true"
    )
