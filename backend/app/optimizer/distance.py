"""Distance and travel time estimates.

Uses the haversine formula for straight line distance and multiplies by a road
factor, which is a common approximation when no routing engine is available.
"""

from math import asin, cos, radians, sin, sqrt

from app.optimizer.types import Location, Problem

EARTH_RADIUS_KM = 6371.0088


def haversine_km(a: Location, b: Location) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (a.lat, a.lng, b.lat, b.lng))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(h))


def distance_matrix_km(points: list[Location], road_factor: float = 1.0) -> list[list[float]]:
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(points[i], points[j]) * road_factor
            matrix[i][j] = matrix[j][i] = d
    return matrix


def travel_minutes(distance_km: float, speed_kmh: float) -> float:
    return distance_km / speed_kmh * 60.0


def node_points(problem: Problem) -> list[Location]:
    """Node 0 is the depot, node i (i >= 1) is problem.jobs[i - 1]."""
    return [problem.depot, *(job.location for job in problem.jobs)]


def route_metrics(
    problem: Problem, matrix: list[list[float]], nodes: list[int]
) -> tuple[float, float]:
    """Distance (km) and duration (min) of depot -> nodes -> depot, including service time."""
    if not nodes:
        return 0.0, 0.0
    path = [0, *nodes, 0]
    dist = sum(matrix[path[k]][path[k + 1]] for k in range(len(path) - 1))
    minutes = travel_minutes(dist, problem.speed_kmh) + problem.service_minutes * len(nodes)
    return round(dist, 2), round(minutes, 1)
