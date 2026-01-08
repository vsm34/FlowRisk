"""
Monte Carlo simulation engine for cash flow stress testing.

Uses discrete monthly time steps with stochastic income and expenses.
Supports multiple scenario types: baseline, decision, job_loss, expense_shock, rate_shock, rent_increase.

NOTE:
We intentionally avoid NumPy here to prevent unstable/experimental wheels on Windows + Python 3.13.
Stdlib random.Random(seed) provides deterministic normal draws via gauss().
"""

import random
from typing import TypedDict

from app.models.debt import Debt
from app.models.financial_profile import FinancialProfile
from app.models.scenario import Scenario


class SimulationResult(TypedDict):
    """Result structure from simulation engine."""

    cash_paths: list[list[float]]  # (n_sims x (H+1))
    failed: list[bool]  # (n_sims,)
    time_to_fail: list[int | None]  # (n_sims,) - month index 1..H or None
    min_cash: list[float]  # (n_sims,)
    debt_payment_paths: list[list[float]]  # (n_sims x H)
    meta: dict  # {horizon_months, n_sims, seed, assumptions_used}


def run_simulation(
    profile: FinancialProfile,
    debts: list[Debt],
    scenario: Scenario | None,
    horizon_months: int,
    n_sims: int,
    seed: int | None,
    assumptions: dict | None = None,
) -> SimulationResult:
    """
    Run Monte Carlo cash flow simulation.

    Args:
        profile: User's financial profile
        debts: List of user's debts
        scenario: Scenario to simulate (None for baseline)
        horizon_months: Simulation horizon in months
        n_sims: Number of simulation paths
        seed: Random seed for reproducibility
        assumptions: Override assumptions (sigmas, etc.)

    Returns:
        SimulationResult with paths, failures, and metadata
    """
    # Resolve assumptions
    assumptions = assumptions or {}
    sigma_income = assumptions.get("sigma_income", float(profile.sigma_income))
    sigma_variable = assumptions.get("sigma_variable", float(profile.sigma_variable))

    # Parse scenario parameters
    scenario_params = scenario.parameters_json if scenario else {}
    scenario_type = scenario.type if scenario else "baseline"

    # Deterministic RNG for the entire run
    rng = random.Random(seed)

    # Base values
    base_income = float(profile.monthly_income)
    base_fixed = float(profile.fixed_expenses)
    base_variable = float(profile.variable_expenses)
    initial_cash = float(profile.liquid_savings)
    base_debt_min = sum(float(d.min_payment) for d in debts)

    # Storage
    cash_paths: list[list[float]] = []
    failed: list[bool] = []
    time_to_fail: list[int | None] = []
    min_cash_list: list[float] = []
    debt_payment_paths: list[list[float]] = []

    for _sim_idx in range(n_sims):
        cash = initial_cash
        path = [cash]
        payments: list[float] = []
        has_failed = False
        fail_month: int | None = None
        path_min = cash

        for month in range(1, horizon_months + 1):
            # Apply scenario shocks
            income = base_income
            fixed = base_fixed
            variable = base_variable
            debt_min = base_debt_min

            # Income shock: job loss
            if scenario_type == "job_loss":
                start_month = int(scenario_params.get("start_month", 1))
                duration_months = int(scenario_params.get("duration_months", 3))
                replacement_pct = float(scenario_params.get("unemployment_replacement_pct", 0.0))
                if start_month <= month < start_month + duration_months:
                    income = base_income * replacement_pct

            # Add stochastic variation to income (if not fully zero)
            if income > 0 and sigma_income > 0:
                # Normal(0, sigma_income)
                income_shock = rng.gauss(0.0, float(sigma_income))
                income = income * (1.0 + income_shock)
                income = max(0.0, income)

            # Variable expenses shock
            if sigma_variable > 0:
                variable_shock = rng.gauss(0.0, float(sigma_variable))
                variable = variable * (1.0 + variable_shock)
                variable = max(0.0, variable)

            # Rent increase
            if scenario_type == "rent_increase":
                start_month = int(scenario_params.get("start_month", 1))
                rent_delta = float(scenario_params.get("rent_delta", 0))
                if month >= start_month:
                    fixed = fixed + rent_delta

            # Rate shock (MVP: min_payment stays constant unless scenario specifies increase)
            if scenario_type == "rate_shock":
                min_payment_increase = float(scenario_params.get("min_payment_increase", 0))
                debt_min = debt_min + min_payment_increase

            # Decision scenario
            if scenario_type == "decision":
                one_time_cost = float(scenario_params.get("one_time_cost", 0))
                extra_monthly_payment = float(scenario_params.get("extra_monthly_payment", 0))
                if month == 1 and one_time_cost > 0:
                    fixed = fixed + one_time_cost
                if extra_monthly_payment > 0:
                    debt_min = debt_min + extra_monthly_payment

            # Expense shock
            if scenario_type == "expense_shock":
                shock_month = int(scenario_params.get("shock_month", 1))
                shock_amount = float(scenario_params.get("shock_amount", 0))
                shock_duration = int(scenario_params.get("shock_duration", 1))
                if shock_month <= month < shock_month + shock_duration:
                    if shock_duration > 1:
                        fixed = fixed + (shock_amount / shock_duration)
                    else:
                        fixed = fixed + shock_amount

            # Cash flow equation
            net_flow = income - fixed - variable - debt_min
            cash_next = cash + net_flow

            # Failure check (enterprise-style)
            if cash_next < 0 or (cash < debt_min and cash + income - fixed - variable < debt_min):
                if not has_failed:
                    has_failed = True
                    fail_month = month
                break

            cash = cash_next
            path.append(cash)
            payments.append(debt_min)
            path_min = min(path_min, cash)

        # Pad paths to horizon if stopped early
        while len(path) < horizon_months + 1:
            path.append(0.0)
        while len(payments) < horizon_months:
            payments.append(0.0)

        cash_paths.append(path)
        failed.append(has_failed)
        time_to_fail.append(fail_month)
        min_cash_list.append(path_min)
        debt_payment_paths.append(payments)

    return SimulationResult(
        cash_paths=cash_paths,
        failed=failed,
        time_to_fail=time_to_fail,
        min_cash=min_cash_list,
        debt_payment_paths=debt_payment_paths,
        meta={
            "horizon_months": horizon_months,
            "n_sims": n_sims,
            "seed": seed,
            "assumptions_used": {
                "sigma_income": sigma_income,
                "sigma_variable": sigma_variable,
            },
        },
    )
