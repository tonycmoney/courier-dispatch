"""Capacitated vehicle routing with time windows, solved with Google OR-Tools.

Model:
  * Node 0 is the depot; every vehicle starts and ends there.
  * Arc cost is road distance in meters.
  * Capacity dimension enforces each vehicle's package limit.
  * Time dimension (travel + service minutes) enforces the shift length and
    any per stop delivery window.
  * Every stop is optional with a drop penalty, so an over constrained
    problem still returns the best partial plan instead of failing. Priority
    stops carry a much larger penalty, so they are dropped last.
"""

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from app.optimizer.distance import distance_matrix_km, node_points, route_metrics, travel_minutes
from app.optimizer.types import Problem, Solution, VehicleRoute

DROP_PENALTY = 1_000_000  # meters; larger than any realistic detour
PRIORITY_DROP_PENALTY = 100_000_000


def solve_vrp(problem: Problem, time_limit_s: int = 3) -> Solution:
    if not problem.jobs or not problem.vehicles:
        return Solution(solver="ortools", routes=[], unassigned=[j.id for j in problem.jobs])

    km = distance_matrix_km(node_points(problem), problem.road_factor)
    meters = [[int(round(d * 1000)) for d in row] for row in km]
    minutes = [[int(round(travel_minutes(d, problem.speed_kmh))) for d in row] for row in km]
    n_nodes = len(km)
    n_vehicles = len(problem.vehicles)

    manager = pywrapcp.RoutingIndexManager(n_nodes, n_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_cb(from_index: int, to_index: int) -> int:
        return meters[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit = routing.RegisterTransitCallback(distance_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit)

    # Capacity
    demands = [0, *(job.demand for job in problem.jobs)]

    def demand_cb(from_index: int) -> int:
        return demands[manager.IndexToNode(from_index)]

    demand_idx = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [v.capacity for v in problem.vehicles], True, "Capacity"
    )

    # Time: travel time plus service time at the origin node (none at depot).
    def time_cb(from_index: int, to_index: int) -> int:
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        service = problem.service_minutes if i != 0 else 0
        return minutes[i][j] + service

    time_idx = routing.RegisterTransitCallback(time_cb)
    horizon = problem.shift_minutes
    routing.AddDimension(time_idx, horizon, horizon, True, "Time")
    time_dim = routing.GetDimensionOrDie("Time")

    for node, job in enumerate(problem.jobs, start=1):
        index = manager.NodeToIndex(node)
        if job.window is not None:
            start, end = job.window
            time_dim.CumulVar(index).SetRange(min(start, horizon), min(end, horizon))
        penalty = PRIORITY_DROP_PENALTY if job.priority else DROP_PENALTY
        routing.AddDisjunction([index], penalty)

    # Encourage balanced, shorter routes rather than one very long one.
    time_dim.SetGlobalSpanCostCoefficient(10)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.seconds = time_limit_s

    assignment = routing.SolveWithParameters(params)
    if assignment is None:
        return Solution(solver="ortools", routes=[], unassigned=[j.id for j in problem.jobs])

    routes: list[VehicleRoute] = []
    visited: set[int] = set()
    for v_idx, vehicle in enumerate(problem.vehicles):
        index = routing.Start(v_idx)
        nodes: list[int] = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                nodes.append(node)
            index = assignment.Value(routing.NextVar(index))
        if not nodes:
            continue
        visited.update(nodes)
        dist, mins = route_metrics(problem, km, nodes)
        routes.append(
            VehicleRoute(
                vehicle_id=vehicle.id,
                job_ids=[problem.jobs[n - 1].id for n in nodes],
                distance_km=dist,
                duration_min=mins,
                load=sum(problem.jobs[n - 1].demand for n in nodes),
            )
        )

    unassigned = [job.id for node, job in enumerate(problem.jobs, start=1) if node not in visited]
    return Solution(solver="ortools", routes=routes, unassigned=unassigned)
