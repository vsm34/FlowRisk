from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProfileUpsertRequest(BaseModel):
    """Request schema for creating/updating financial profile."""
    
    monthly_income: Decimal
    sigma_income: Decimal = Decimal("0.05")
    fixed_expenses: Decimal
    variable_expenses: Decimal
    sigma_variable: Decimal = Decimal("0.10")
    liquid_savings: Decimal
    assumptions_json: dict | None = None


class DebtInProfile(BaseModel):
    """Debt schema for inclusion in profile response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    balance: Decimal
    apr: Decimal
    min_payment: Decimal


class ProfileResponse(BaseModel):
    """Response schema for financial profile."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    monthly_income: Decimal
    sigma_income: Decimal
    fixed_expenses: Decimal
    variable_expenses: Decimal
    sigma_variable: Decimal
    liquid_savings: Decimal
    assumptions_json: dict | None
    created_at: datetime
    updated_at: datetime
    debts: list[DebtInProfile] = []
