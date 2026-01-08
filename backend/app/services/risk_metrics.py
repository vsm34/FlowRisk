"""
Risk metrics computation and chart data generation.

Computes summary statistics from simulation results:
- Failure probability
- Time-to-fail quantiles (for failed paths)
- Minimum cash quantiles
- Cash trajectory quantiles for charting
"""

from app.services.simulation_engine import SimulationResult


def quantile(data: list[float], p: float) -> float:
    """
    Compute quantile using linear interpolation.
    
    Args:
        data: Sorted or unsorted data
        p: Quantile probability (0.0 to 1.0)
        
    Returns:
        Quantile value
    """
    if not data:
        return 0.0
    
    sorted_data = sorted(data)
    n = len(sorted_data)
    
    if n == 1:
        return sorted_data[0]
    
    # Linear interpolation method
    idx = p * (n - 1)
    lower_idx = int(idx)
    upper_idx = min(lower_idx + 1, n - 1)
    weight = idx - lower_idx
    
    return sorted_data[lower_idx] * (1 - weight) + sorted_data[upper_idx] * weight


def compute_summary(sim_result: SimulationResult) -> dict:
    """
    Compute summary risk metrics from simulation result.
    
    Args:
        sim_result: Simulation result from engine
        
    Returns:
        Dictionary with summary metrics and chart data
    """
    n_sims = len(sim_result["failed"])
    n_failed = sum(sim_result["failed"])
    p_fail = n_failed / n_sims if n_sims > 0 else 0.0
    
    # Time to fail statistics (only for failed paths)
    failed_times = [
        t for t in sim_result["time_to_fail"] if t is not None
    ]
    time_to_fail_stats = {}
    if failed_times:
        time_to_fail_stats = {
            "p10": quantile(failed_times, 0.10),
            "p50": quantile(failed_times, 0.50),
            "p90": quantile(failed_times, 0.90),
            "median": quantile(failed_times, 0.50),
        }
    
    # Minimum cash statistics
    min_cash_stats = {
        "p10": quantile(sim_result["min_cash"], 0.10),
        "p50": quantile(sim_result["min_cash"], 0.50),
        "p90": quantile(sim_result["min_cash"], 0.90),
    }
    
    # Cash trajectory quantiles per month
    horizon = sim_result["meta"]["horizon_months"]
    cash_paths = sim_result["cash_paths"]
    
    months = list(range(horizon + 1))
    cash_p10 = []
    cash_p50 = []
    cash_p90 = []
    
    for month_idx in range(horizon + 1):
        month_cash = [path[month_idx] for path in cash_paths]
        cash_p10.append(quantile(month_cash, 0.10))
        cash_p50.append(quantile(month_cash, 0.50))
        cash_p90.append(quantile(month_cash, 0.90))
    
    # Debt service burden (average)
    avg_debt_payment = 0.0
    if sim_result["debt_payment_paths"]:
        all_payments = [
            p for path in sim_result["debt_payment_paths"] for p in path if p > 0
        ]
        avg_debt_payment = sum(all_payments) / len(all_payments) if all_payments else 0.0
    
    summary = {
        "p_fail": round(p_fail, 4),
        "n_failed": n_failed,
        "n_sims": n_sims,
        "time_to_fail": time_to_fail_stats,
        "min_cash": min_cash_stats,
        "avg_debt_payment": round(avg_debt_payment, 2),
    }
    
    chart_data = {
        "months": months,
        "cash_p10": [round(v, 2) for v in cash_p10],
        "cash_p50": [round(v, 2) for v in cash_p50],
        "cash_p90": [round(v, 2) for v in cash_p90],
    }
    
    return {
        "summary": summary,
        "chart": chart_data,
    }
