from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DebtCreateRequest(BaseModel):
    """Request schema for creating a debt."""
    
    name: str
    balance: Decimal
    apr: Decimal  # Decimal fraction (e.g., 0.0499 for 4.99%)
    min_payment: Decimal


class DebtResponse(BaseModel):
    """Response schema for debt."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    profile_id: int
    name: str
    balance: Decimal
    apr: Decimal
    min_payment: Decimal
    created_at: datetime
    updated_at: datetime
