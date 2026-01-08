from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.scenario import (
    ScenarioCreateRequest,
    ScenarioResponse,
    ScenarioUpdateRequest,
)

router = APIRouter()


@router.get("/v1/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all scenarios for current user."""
    scenarios = (
        db.query(Scenario)
        .filter(Scenario.user_id == current_user.id)
        .order_by(Scenario.created_at.desc())
        .all()
    )
    return scenarios


@router.post("/v1/scenarios", response_model=ScenarioResponse, status_code=201)
async def create_scenario(
    request: ScenarioCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new scenario for current user."""
    scenario = Scenario(
        user_id=current_user.id,
        **request.model_dump(),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/v1/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get a specific scenario (must belong to current user)."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Verify ownership
    if scenario.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return scenario


@router.put("/v1/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    request: ScenarioUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a scenario (must belong to current user)."""
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Verify ownership
    if scenario.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)
    
    db.commit()
    db.refresh(scenario)
    return scenario
