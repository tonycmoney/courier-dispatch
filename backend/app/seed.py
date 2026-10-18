"""Demo data: a small courier operation in central Connecticut."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Driver, Plan, Route, Stop

DRIVERS = [
    {"name": "Marcus R.", "vehicle": "cargo_van", "capacity": 40},
    {"name": "Dana P.", "vehicle": "minivan", "capacity": 20},
    {"name": "Luis G.", "vehicle": "cargo_van", "capacity": 40},
]

# (label, address, lat, lng, packages, priority, window)
STOPS = [
    ("Hartford Hospital Lab", "80 Seymour St, Hartford", 41.7547, -72.6787, 4, True, (0, 180)),
    ("Yale New Haven Pharmacy", "20 York St, New Haven", 41.3036, -72.9363, 3, True, (60, 240)),
    ("MidState Medical Center", "435 Lewis Ave, Meriden", 41.5469, -72.7926, 5, False, None),
    ("Waterbury Clinic", "64 Robbins St, Waterbury", 41.5604, -73.0349, 2, False, None),
    ("Bristol Imaging", "86 Lake Ave, Bristol", 41.6787, -72.9409, 3, False, None),
    ("New Britain Lab Draw", "100 Grand St, New Britain", 41.6633, -72.7826, 2, False, None),
    ("Wallingford Dental", "50 N Main St, Wallingford", 41.4570, -72.8231, 1, False, None),
    ("Hamden Urgent Care", "2080 Whitney Ave, Hamden", 41.3825, -72.9029, 2, True, (0, 120)),
    ("Southington Family Practice", "1 Center Pl, Southington", 41.5965, -72.8776, 3, False, None),
    ("Middletown Records Office", "245 DeKoven Dr, Middletown", 41.5623, -72.6506, 6, False, None),
    ("West Hartford Pediatrics", "21 S Main St, West Hartford", 41.7621, -72.7420, 2, False, None),
    ("Branford Pharmacy", "1060 Main St, Branford", 41.2795, -72.8151, 2, False, None),
    ("Naugatuck Physical Therapy", "607 Rubber Ave, Naugatuck", 41.4890, -73.0715, 1, False, None),
    (
        "Farmington Surgical",
        "263 Farmington Ave, Farmington",
        41.7298,
        -72.7952,
        4,
        True,
        (120, 300),
    ),
    ("Milford Diagnostics", "300 Seemans Ln, Milford", 41.2307, -73.0640, 3, False, None),
    ("East Haven Clinic", "250 Main St, East Haven", 41.2762, -72.8682, 2, False, None),
    ("Berlin Veterinary", "880 Farmington Ave, Berlin", 41.6215, -72.7457, 1, False, None),
    ("Cromwell Rehab", "100 Berlin Rd, Cromwell", 41.5951, -72.6726, 2, False, None),
]


def seed(db: Session) -> None:
    for d in DRIVERS:
        db.add(Driver(**d))
    for label, address, lat, lng, packages, priority, window in STOPS:
        db.add(
            Stop(
                label=label,
                address=address,
                lat=lat,
                lng=lng,
                packages=packages,
                priority=priority,
                window_start=window[0] if window else None,
                window_end=window[1] if window else None,
            )
        )
    db.commit()


def seed_if_empty(db: Session) -> bool:
    if db.scalars(select(Driver).limit(1)).first() is not None:
        return False
    seed(db)
    return True


def reset(db: Session) -> None:
    for model in (Route, Plan, Stop, Driver):
        db.execute(delete(model))
    db.commit()
    seed(db)
