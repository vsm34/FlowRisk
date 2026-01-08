"""
Explainability via OAT (One-At-a-Time) sensitivity analysis.

Identifies key drivers of financial risk by perturbing inputs one at a time
and measuring impact on failure probability.
"""

from copy import deepcopy
from decimal import Decimal

from app.models.debt import Debt
from app.models.financial_profile import FinancialProfile
from app.models.scenario import Scenario
from app.services.simulation_engine import run_simulation


def D(x: str) -> Decimal:
    """Helper to create Decimal from string literal."""
    return Decimal(x)


def _to_jsonable(obj):
    """Recursively convert Decimal values to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_to_jsonable(item) for item in obj]
    return obj


def compute_oat_drivers(
    profile: FinancialProfile,
    debts: list[Debt],
    scenario: Scenario | None,
    horizon_months: int,
    n_sims: int,
    seed: int | None,
    assumptions: dict | None = None,
) -> list[dict]:
    """
    Compute OAT sensitivity drivers.
    
    Runs baseline scenario and perturbations to identify key risk drivers.
    Returns drivers ranked by absolute impact on failure probability.
    
    Args:
        profile: User's financial profile
        debts: List of user's debts
        scenario: Scenario to analyze
        horizon_months: Simulation horizon
        n_sims: Number of simulations
        seed: Random seed
        assumptions: Override assumptions
        
    Returns:
        List of driver dicts with name and delta_p_fail, sorted by abs impact
    """
    # Run baseline
    baseline_result = run_simulation(
        profile, debts, scenario, horizon_months, n_sims, seed, assumptions
    )
    n_failed_base = sum(baseline_result["failed"])
    p_fail_base = n_failed_base / n_sims if n_sims > 0 else 0.0
    
    drivers = []
    
    # Perturbation 1: +10% liquid savings
    profile_dict = {
        "monthly_income": profile.monthly_income,
        "sigma_income": profile.sigma_income,
        "fixed_expenses": profile.fixed_expenses,
        "variable_expenses": profile.variable_expenses,
        "sigma_variable": profile.sigma_variable,
        "liquid_savings": profile.liquid_savings * D("1.10"),
    }
    temp_profile = type("TempProfile", (), profile_dict)()
    result = run_simulation(
        temp_profile, debts, scenario, horizon_months, n_sims, seed, assumptions
    )
    p_fail = sum(result["failed"]) / n_sims if n_sims > 0 else 0.0
    drivers.append({
        "driver": "liquidity +10%",
        "delta_p_fail": round(p_fail_base - p_fail, 4),
    })
    
    # Perturbation 2: -10% fixed expenses
    profile_dict = {
        "monthly_income": profile.monthly_income,
        "sigma_income": profile.sigma_income,
        "fixed_expenses": profile.fixed_expenses * D("0.90"),
        "variable_expenses": profile.variable_expenses,
        "sigma_variable": profile.sigma_variable,
        "liquid_savings": profile.liquid_savings,
    }
    temp_profile = type("TempProfile", (), profile_dict)()
    result = run_simulation(
        temp_profile, debts, scenario, horizon_months, n_sims, seed, assumptions
    )
    p_fail = sum(result["failed"]) / n_sims if n_sims > 0 else 0.0
    drivers.append({
        "driver": "fixed_expenses -10%",
        "delta_p_fail": round(p_fail_base - p_fail, 4),
    })
    
    # Perturbation 3: -10% variable expenses
    profile_dict = {
        "monthly_income": profile.monthly_income,
        "sigma_income": profile.sigma_income,
        "fixed_expenses": profile.fixed_expenses,
        "variable_expenses": profile.variable_expenses * D("0.90"),
        "sigma_variable": profile.sigma_variable,
        "liquid_savings": profile.liquid_savings,
    }
    temp_profile = type("TempProfile", (), profile_dict)()
    result = run_simulation(
        temp_profile, debts, scenario, horizon_months, n_sims, seed, assumptions
    )
    p_fail = sum(result["failed"]) / n_sims if n_sims > 0 else 0.0
    drivers.append({
        "driver": "variable_expenses -10%",
        "delta_p_fail": round(p_fail_base - p_fail, 4),
    })
    
    # Perturbation 4: +10% income
    profile_dict = {
        "monthly_income": profile.monthly_income * D("1.10"),
        "sigma_income": profile.sigma_income,
        "fixed_expenses": profile.fixed_expenses,
        "variable_expenses": profile.variable_expenses,
        "sigma_variable": profile.sigma_variable,
        "liquid_savings": profile.liquid_savings,
    }
    temp_profile = type("TempProfile", (), profile_dict)()
    result = run_simulation(
        temp_profile, debts, scenario, horizon_months, n_sims, seed, assumptions
    )
    p_fail = sum(result["failed"]) / n_sims if n_sims > 0 else 0.0
    drivers.append({
        "driver": "income +10%",
        "delta_p_fail": round(p_fail_base - p_fail, 4),
    })
    
    # Perturbation 5: Remove shock (baseline scenario)
    if scenario is not None:
        result = run_simulation(
            profile, debts, None, horizon_months, n_sims, seed, assumptions
        )
        p_fail = sum(result["failed"]) / n_sims if n_sims > 0 else 0.0
        drivers.append({
            "driver": "remove shock",
            "delta_p_fail": round(p_fail_base - p_fail, 4),
        })
    
    # Sort by absolute impact descending
    drivers.sort(key=lambda x: abs(x["delta_p_fail"]), reverse=True)
    
    # Convert Decimal values to float for JSON serialization
    return _to_jsonable(drivers)
