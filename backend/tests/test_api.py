from app.seed import DRIVERS, STOPS

NEW_STOP = {"label": "Test Clinic", "lat": 41.55, "lng": -72.9, "packages": 2}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_driver_crud(client):
    created = client.post("/api/drivers", json={"name": "Ana", "capacity": 25})
    assert created.status_code == 201
    driver_id = created.json()["id"]

    updated = client.patch(f"/api/drivers/{driver_id}", json={"active": False})
    assert updated.json()["active"] is False
    assert updated.json()["capacity"] == 25

    assert client.delete(f"/api/drivers/{driver_id}").status_code == 204
    assert client.patch(f"/api/drivers/{driver_id}", json={"name": "x"}).status_code == 404


def test_driver_validation(client):
    assert client.post("/api/drivers", json={"name": "", "capacity": 10}).status_code == 422
    assert client.post("/api/drivers", json={"name": "A", "capacity": 0}).status_code == 422
    assert client.post("/api/drivers", json={"name": "A", "vehicle": "bike"}).status_code == 422


def test_stop_create_and_filter(client):
    assert client.post("/api/stops", json=NEW_STOP).status_code == 201
    assert len(client.get("/api/stops").json()) == 1
    assert len(client.get("/api/stops?status=pending").json()) == 1
    assert client.get("/api/stops?status=delivered").json() == []


def test_stop_window_validation(client):
    bad = {**NEW_STOP, "window_start": 100}
    assert client.post("/api/stops", json=bad).status_code == 422
    bad = {**NEW_STOP, "window_start": 100, "window_end": 50}
    assert client.post("/api/stops", json=bad).status_code == 422
    good = {**NEW_STOP, "window_start": 50, "window_end": 100}
    assert client.post("/api/stops", json=good).status_code == 201


def test_status_state_machine(client):
    stop_id = client.post("/api/stops", json=NEW_STOP).json()["id"]

    def move(status):
        return client.patch(f"/api/stops/{stop_id}/status", json={"status": status})

    assert move("delivered").status_code == 409  # cannot skip ahead
    assert move("assigned").status_code == 200
    assert move("in_transit").status_code == 200
    assert client.delete(f"/api/stops/{stop_id}").status_code == 409  # in transit
    assert move("failed").status_code == 200
    assert move("pending").status_code == 200  # retry a failed delivery
    assert move("assigned").status_code == 200
    assert move("in_transit").status_code == 200
    assert move("delivered").status_code == 200
    assert move("pending").status_code == 409  # delivered is final


def test_summary(seeded_client):
    data = seeded_client.get("/api/summary").json()
    assert data["drivers_active"] == len(DRIVERS)
    assert data["stops_total"] == len(STOPS)
    assert data["stops_by_status"]["pending"] == len(STOPS)
    assert data["packages_pending"] == sum(s[4] for s in STOPS)


def test_optimize_requires_drivers_and_stops(client):
    assert client.post("/api/dispatch/optimize", json={}).status_code == 422
    client.post("/api/drivers", json={"name": "Ana"})
    assert client.post("/api/dispatch/optimize", json={}).status_code == 422


def test_optimize_creates_plan_and_assigns_stops(seeded_client):
    assert seeded_client.get("/api/dispatch/plans/latest").json() is None

    res = seeded_client.post("/api/dispatch/optimize", json={"solver": "ortools"})
    assert res.status_code == 201
    plan = res.json()
    assert plan["unassigned"] == []
    assert plan["total_distance_km"] > 0
    for route in plan["routes"]:
        assert route["load"] <= route["capacity"]
        # Path starts and ends at the depot, with one point per stop between.
        assert route["path"][0] == route["path"][-1]
        assert len(route["path"]) == len(route["stop_ids"]) + 2

    stops = seeded_client.get("/api/stops").json()
    assert all(s["status"] == "assigned" for s in stops)
    assert seeded_client.get("/api/dispatch/plans/latest").json()["id"] == plan["id"]


def test_reoptimize_skips_in_transit_stops(seeded_client):
    seeded_client.post("/api/dispatch/optimize", json={"solver": "heuristic"})
    seeded_client.patch("/api/stops/1/status", json={"status": "in_transit"})
    plan = seeded_client.post("/api/dispatch/optimize", json={"solver": "heuristic"}).json()
    planned = {sid for r in plan["routes"] for sid in r["stop_ids"]}
    assert 1 not in planned


def test_inactive_drivers_not_used(seeded_client):
    seeded_client.patch("/api/drivers/1", json={"active": False})
    plan = seeded_client.post("/api/dispatch/optimize", json={"solver": "heuristic"}).json()
    assert all(r["driver_id"] != 1 for r in plan["routes"])


def test_demo_reset(seeded_client):
    seeded_client.post("/api/dispatch/optimize", json={"solver": "heuristic"})
    assert seeded_client.post("/api/demo/reset").status_code == 204
    assert seeded_client.get("/api/dispatch/plans/latest").json() is None
    assert seeded_client.get("/api/summary").json()["stops_by_status"]["pending"] == len(STOPS)
