import pytest

from app.optimizer import Job, Location, Problem, Vehicle, solve
from app.optimizer.distance import haversine_km
from app.optimizer.heuristic import _two_opt
from app.seed import DRIVERS, STOPS

DEPOT = Location(41.4990, -72.9007)
SOLVERS = ["heuristic", "ortools"]


def demo_problem(**overrides) -> Problem:
    jobs = [
        Job(i + 1, Location(lat, lng), packages, priority, window)
        for i, (_, _, lat, lng, packages, priority, window) in enumerate(STOPS)
    ]
    vehicles = [Vehicle(i + 1, d["capacity"]) for i, d in enumerate(DRIVERS)]
    kwargs = {"depot": DEPOT, "vehicles": vehicles, "jobs": jobs, **overrides}
    return Problem(**kwargs)


def test_haversine_known_distance():
    # Hartford to New Haven is roughly 50 km in a straight line.
    hartford = Location(41.7658, -72.6734)
    new_haven = Location(41.3083, -72.9279)
    assert haversine_km(hartford, new_haven) == pytest.approx(55.3, abs=1.5)


def test_haversine_zero_and_symmetric():
    a, b = Location(41.5, -72.9), Location(41.7, -72.6)
    assert haversine_km(a, a) == 0
    assert haversine_km(a, b) == pytest.approx(haversine_km(b, a))


def test_two_opt_removes_crossing():
    # Square with a crossing order: depot(0) -> 1 -> 3 -> 2 -> 4 -> depot
    pts = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0.5)]
    matrix = [[((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for b in pts] for a in pts]

    def length(order):
        path = [0, *order, 0]
        return sum(matrix[path[i]][path[i + 1]] for i in range(len(path) - 1))

    crossing = [1, 3, 2]
    improved = _two_opt(crossing, matrix)
    assert length(improved) < length(crossing)
    assert sorted(improved) == sorted(crossing)


@pytest.mark.parametrize("solver", SOLVERS)
def test_every_stop_served_exactly_once(solver):
    problem = demo_problem()
    solution = solve(problem, solver, time_limit_s=1)
    served = [jid for r in solution.routes for jid in r.job_ids]
    assert len(served) == len(set(served))
    assert set(served) | set(solution.unassigned) == {j.id for j in problem.jobs}
    assert solution.unassigned == []


@pytest.mark.parametrize("solver", SOLVERS)
def test_capacity_respected(solver):
    problem = demo_problem()
    capacity = {v.id: v.capacity for v in problem.vehicles}
    demand = {j.id: j.demand for j in problem.jobs}
    for route in solve(problem, solver, time_limit_s=1).routes:
        assert route.load == sum(demand[j] for j in route.job_ids)
        assert route.load <= capacity[route.vehicle_id]


@pytest.mark.parametrize("solver", SOLVERS)
def test_shift_length_respected(solver):
    problem = demo_problem()
    for route in solve(problem, solver, time_limit_s=1).routes:
        assert route.duration_min <= problem.shift_minutes


@pytest.mark.parametrize("solver", SOLVERS)
def test_over_capacity_drops_stops_not_priority(solver):
    # One small van cannot carry everything; priority stops must be kept.
    problem = demo_problem(vehicles=[Vehicle(1, 15)])
    solution = solve(problem, solver, time_limit_s=1)
    assert solution.unassigned, "expected some stops to be dropped"
    priority_ids = {j.id for j in problem.jobs if j.priority}
    assert priority_ids.isdisjoint(solution.unassigned)


def test_ortools_honors_time_windows():
    problem = demo_problem()
    jobs = {j.id: j for j in problem.jobs}
    solution = solve(problem, "ortools", time_limit_s=1)
    # Recompute arrival times along each route and check windows.
    from app.optimizer.distance import travel_minutes

    for route in solution.routes:
        clock = 0.0
        prev = DEPOT
        for jid in route.job_ids:
            job = jobs[jid]
            clock += travel_minutes(haversine_km(prev, job.location) * problem.road_factor, 50)
            if job.window:
                clock = max(clock, job.window[0])
                # Allow a couple minutes for integer rounding inside the solver.
                assert clock <= job.window[1] + 3, f"stop {jid} arrives at {clock:.0f}"
            clock += problem.service_minutes
            prev = job.location


def test_ortools_beats_or_matches_heuristic():
    problem = demo_problem()
    exact = solve(problem, "ortools", time_limit_s=1)
    baseline = solve(problem, "heuristic")
    assert exact.total_distance_km <= baseline.total_distance_km


@pytest.mark.parametrize("solver", SOLVERS)
def test_empty_problem(solver):
    solution = solve(Problem(DEPOT, [Vehicle(1, 10)], []), solver)
    assert solution.routes == []
    assert solution.unassigned == []


def test_unknown_solver():
    with pytest.raises(ValueError):
        solve(demo_problem(), "magic")
