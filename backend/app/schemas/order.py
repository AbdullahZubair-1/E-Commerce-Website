import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator
from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    shipping_address: str
    notes: Optional[str] = None

    @field_validator("shipping_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Shipping address must be at least 10 characters")
        if len(v) > 500:
            raise ValueError("Shipping address is too long")
        return v


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    product_name: str
    product_price: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    notes: Optional[str] = None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderSummaryResponse(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    shipping_address: str
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
