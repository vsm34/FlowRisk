import logging
from random import randint
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.scenario import Scenario
from app.models.stress_test_result import StressTestResult
from app.models.stress_test_run import StressTestRun
from app.models.user import User
from app.schemas.runs import (
    RunCreateRequest,
    RunCreateResponse,
    RunListItem,
    RunResultResponse,
)
from app.services.explainability import compute_oat_drivers
from app.services.risk_metrics import compute_summary
from app.services.simulation_engine import run_simulation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/v1/runs", response_model=RunCreateResponse, status_code=201)
async def create_run(
    request: RunCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create and execute a new stress test run.

    Runs Monte Carlo simulation, computes risk metrics and drivers,
    and persists results to database.
    """
    # Load user's financial profile
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Create a financial profile first.",
        )

    # Load debts
    debts = profile.debts

    # Load scenario if specified
    scenario = None
    if request.scenario_id is not None:
        scenario = (
            db.query(Scenario)
            .filter(
                Scenario.id == request.scenario_id,
                Scenario.user_id == current_user.id,
            )
            .first()
        )

        if not scenario:
            raise HTTPException(
                status_code=404,
                detail="Scenario not found or does not belong to user.",
            )

    # Generate seed if not provided
    seed = request.seed if request.seed is not None else randint(0, 2**31 - 1)

    # Resolve assumptions (store AND use the resolved values)
    # Accept both "sigma_variable" and "sigma_var" for compatibility
    assumptions_in = request.assumptions or {}
    sigma_var_value = assumptions_in.get("sigma_variable") or assumptions_in.get("sigma_var")
    assumptions_used = {
        "sigma_income": float(assumptions_in.get("sigma_income", float(profile.sigma_income))),
        "sigma_variable": float(sigma_var_value if sigma_var_value is not None else float(profile.sigma_variable)),
    }

    # Run simulation and compute metrics with error handling
    try:
        # Run simulation (FIX: use assumptions_used)
        sim_result = run_simulation(
            profile=profile,
            debts=debts,
            scenario=scenario,
            horizon_months=request.horizon_months,
            n_sims=request.n_sims,
            seed=seed,
            assumptions=assumptions_used,
        )

        # Compute risk metrics and chart data
        metrics_result = compute_summary(sim_result)
        summary = metrics_result["summary"]
        chart = metrics_result["chart"]

        # Compute OAT drivers (FIX: use assumptions_used)
        drivers = compute_oat_drivers(
            profile=profile,
            debts=debts,
            scenario=scenario,
            horizon_months=request.horizon_months,
            n_sims=request.n_sims,
            seed=seed,
            assumptions=assumptions_used,
        )
    except Exception as e:
        logger.exception(
            "Run computation failed",
            extra={
                "user_id": current_user.id,
                "scenario_id": request.scenario_id,
                "horizon_months": request.horizon_months,
                "n_sims": request.n_sims,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Run computation failed. Please check your inputs and try again.",
        )

    # Create run record
    run = StressTestRun(
        user_id=current_user.id,
        scenario_id=request.scenario_id,
        horizon_months=request.horizon_months,
        n_sims=request.n_sims,
        seed=seed,
        assumptions_json=assumptions_used,
    )
    db.add(run)
    db.flush()  # Get run.id

    # Create result record
    result = StressTestResult(
        run_id=run.id,
        summary_metrics_json=summary,
        drivers_json=drivers,
        chart_data_json=chart,
    )
    db.add(result)
    db.commit()

    # Log for monitoring
    logger.info(
        f"Stress test run created: run_id={run.id}, user_id={current_user.id}, "
        f"scenario_id={request.scenario_id}, p_fail={summary['p_fail']}"
    )

    return RunCreateResponse(run_id=run.id)


@router.get("/v1/runs", response_model=list[RunListItem])
async def list_runs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all stress test runs for current user."""
    runs = (
        db.query(StressTestRun)
        .filter(StressTestRun.user_id == current_user.id)
        .order_by(StressTestRun.created_at.desc())
        .all()
    )
    return runs


@router.get("/v1/runs/{run_id}", response_model=RunResultResponse)
async def get_run_result(
    run_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get stress test run results (must belong to current user)."""

    # FIX: ownership-scoped query (prevents leaking that a run_id exists)
    run = (
        db.query(StressTestRun)
        .filter(
            StressTestRun.id == run_id,
            StressTestRun.user_id == current_user.id,
        )
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Load result
    result = (
        db.query(StressTestResult)
        .filter(StressTestResult.run_id == run_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Build response
    run_data = {
        "id": run.id,
        "scenario_id": run.scenario_id,
        "horizon_months": run.horizon_months,
        "n_sims": run.n_sims,
        "seed": run.seed,
        "assumptions": run.assumptions_json,
        "created_at": run.created_at.isoformat(),
    }

    return RunResultResponse(
        run=run_data,
        summary=result.summary_metrics_json,
        drivers=result.drivers_json,
        chart=result.chart_data_json,
    )
