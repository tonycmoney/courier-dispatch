"""Route optimization package.

`solve()` is the single entry point. Solvers work on plain dataclasses, so they
can be tested without a database or web server.
"""

from app.optimizer.heuristic import solve_heuristic
from app.optimizer.types import Job, Location, Problem, Solution, Vehicle, VehicleRoute
from app.optimizer.vrp import solve_vrp

__all__ = [
    "Job",
    "Location",
    "Problem",
    "Solution",
    "Vehicle",
    "VehicleRoute",
    "solve",
    "solve_heuristic",
    "solve_vrp",
]


def solve(problem: Problem, solver: str = "ortools", time_limit_s: int = 3) -> Solution:
    if solver == "heuristic":
        return solve_heuristic(problem)
    if solver == "ortools":
        return solve_vrp(problem, time_limit_s=time_limit_s)
    raise ValueError(f"Unknown solver: {solver}")
