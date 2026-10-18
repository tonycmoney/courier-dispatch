"""Dependency free fallback solver: nearest neighbor construction plus 2-opt.

Fast and predictable. It respects vehicle capacity and shift length, serves
priority stops first, and ignores delivery windows (the OR-Tools solver
handles those). Useful as a baseline to compare the exact solver against.
"""

from app.optimizer.distance import distance_matrix_km, node_points, route_metrics
from app.optimizer.types import Problem, Solution, VehicleRoute


def _two_opt(nodes: list[int], matrix: list[list[float]]) -> list[int]:
    """Reverse segments while doing so shortens the closed tour depot -> nodes -> depot."""
    if len(nodes) < 3:
        return nodes
    best = [0, *nodes, 0]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                a, b = best[i - 1], best[i]
                c, d = best[j], best[j + 1]
                delta = matrix[a][c] + matrix[b][d] - matrix[a][b] - matrix[c][d]
                if delta < -1e-9:
                    best[i : j + 1] = reversed(best[i : j + 1])
                    improved = True
    return best[1:-1]


def solve_heuristic(problem: Problem) -> Solution:
    matrix = distance_matrix_km(node_points(problem), problem.road_factor)
    # Node index for each job, priority jobs considered first.
    remaining = sorted(
        range(1, len(problem.jobs) + 1),
        key=lambda n: not problem.jobs[n - 1].priority,
    )
    routes: list[VehicleRoute] = []

    for vehicle in sorted(problem.vehicles, key=lambda v: -v.capacity):
        if not remaining:
            break
        nodes: list[int] = []
        load = 0
        current = 0
        while True:
            # Prefer priority jobs while any are left, then nearest overall.
            pool = [n for n in remaining if problem.jobs[n - 1].priority] or remaining
            candidates = [n for n in pool if load + problem.jobs[n - 1].demand <= vehicle.capacity]
            candidates = [
                n
                for n in candidates
                if route_metrics(problem, matrix, [*nodes, n])[1] <= problem.shift_minutes
            ]
            if not candidates and pool is not remaining:
                # No feasible priority job; fall back to any job.
                candidates = [
                    n
                    for n in remaining
                    if load + problem.jobs[n - 1].demand <= vehicle.capacity
                    and route_metrics(problem, matrix, [*nodes, n])[1] <= problem.shift_minutes
                ]
            if not candidates:
                break
            nxt = min(candidates, key=lambda n: matrix[current][n])
            nodes.append(nxt)
            load += problem.jobs[nxt - 1].demand
            remaining.remove(nxt)
            current = nxt

        if nodes:
            nodes = _two_opt(nodes, matrix)
            dist, minutes = route_metrics(problem, matrix, nodes)
            routes.append(
                VehicleRoute(
                    vehicle_id=vehicle.id,
                    job_ids=[problem.jobs[n - 1].id for n in nodes],
                    distance_km=dist,
                    duration_min=minutes,
                    load=load,
                )
            )

    return Solution(
        solver="heuristic",
        routes=routes,
        unassigned=[problem.jobs[n - 1].id for n in remaining],
    )
