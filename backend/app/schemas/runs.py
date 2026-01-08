from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RunCreateRequest(BaseModel):
    """Request schema for creating a stress test run."""
    
    scenario_id: int | None = None  # None means baseline
    horizon_months: int = Field(default=12, ge=1, le=24)
    n_sims: int = Field(default=1000, ge=100, le=5000)
    seed: int | None = None
    assumptions: dict | None = None  # Optional overrides for sigmas, etc.


class RunCreateResponse(BaseModel):
    """Response schema for run creation."""
    
    run_id: int


class RunListItem(BaseModel):
    """List item schema for stress test runs."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    scenario_id: int | None
    horizon_months: int
    n_sims: int
    created_at: datetime


class RunResultResponse(BaseModel):
    """Response schema for stress test run results."""
    
    run: dict  # Run metadata
    summary: dict  # Summary metrics
    drivers: list[dict]  # OAT sensitivity drivers
    chart: dict  # Chart data
