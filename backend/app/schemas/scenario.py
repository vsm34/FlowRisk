from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScenarioCreateRequest(BaseModel):
    """Request schema for creating a scenario."""
    
    name: str
    type: str  # baseline, decision, job_loss, expense_shock, rate_shock, rent_increase
    parameters_json: dict = {}


class ScenarioUpdateRequest(BaseModel):
    """Request schema for updating a scenario."""
    
    name: str | None = None
    type: str | None = None
    parameters_json: dict | None = None


class ScenarioResponse(BaseModel):
    """Response schema for scenario."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    type: str
    parameters_json: dict
    created_at: datetime
    updated_at: datetime
