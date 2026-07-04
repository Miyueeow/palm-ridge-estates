"""
Generates fictional subdivision lot data for "Palm Ridge Estates"
Sited on real coordinates near Lipa City, Batangas, Philippines (~13.9411 N, 121.1631 E)

Produces:
- lots.csv          -> full lots table
- amenities.csv      -> POIs within the subdivision
- sales_log.csv      -> event log for time-series / sales velocity analysis
- lots.json          -> same lot data, JSON, for embedding directly in the web map
"""

import csv
import json
import os
import random
from datetime import date, timedelta

random.seed(42)

# Resolve paths relative to this script, so it works regardless of the
# directory it's run from. Output goes to ../data/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---- Site anchor (real-world coordinate near Lipa City, Batangas) ----
ANCHOR_LAT = 13.9411
ANCHOR_LNG = 121.1631

# Local grid spacing in degrees (roughly translates to ~10-12m per lot frontage)
LOT_LAT_STEP = 0.00011   # north-south spacing between rows
LOT_LNG_STEP = 0.00014   # east-west spacing between lots in a row

PHASES = [1, 2, 3]
BLOCKS_PER_PHASE = 4
LOTS_PER_BLOCK = 8

LOT_TYPES = ["interior", "corner", "cul-de-sac"]
LOT_TYPE_WEIGHTS = [0.65, 0.25, 0.10]

STATUS_WEIGHTS = {
    1: {"sold": 0.75, "reserved": 0.15, "available": 0.10},   # Phase 1: oldest, mostly sold
    2: {"sold": 0.45, "reserved": 0.25, "available": 0.30},   # Phase 2: mid
    3: {"sold": 0.10, "reserved": 0.20, "available": 0.70},   # Phase 3: newest, mostly available
}

PHASE_LAUNCH_DATE = {
    1: date(2024, 6, 1),
    2: date(2025, 3, 1),
    3: date(2025, 12, 1),
}

TODAY = date(2026, 7, 4)

lots = []
sales_log = []
lot_counter = 1

for phase in PHASES:
    phase_row_offset = (phase - 1) * (BLOCKS_PER_PHASE + 1)  # gap between phases
    for block in range(1, BLOCKS_PER_PHASE + 1):
        row = phase_row_offset + block
        for i in range(LOTS_PER_BLOCK):
            lot_id = f"LOT-{lot_counter:04d}"
            lat = ANCHOR_LAT + row * LOT_LAT_STEP
            lng = ANCHOR_LNG + i * LOT_LNG_STEP

            lot_type = random.choices(LOT_TYPES, weights=LOT_TYPE_WEIGHTS)[0]
            area_sqm = random.choice([90, 100, 110, 120, 135, 150, 180, 200])
            if lot_type == "corner":
                area_sqm += random.choice([10, 20, 30])
            elif lot_type == "cul-de-sac":
                area_sqm += random.choice([20, 40])

            price_per_sqm = random.randint(14000, 24000)
            price_php = area_sqm * price_per_sqm

            status = random.choices(
                list(STATUS_WEIGHTS[phase].keys()),
                weights=list(STATUS_WEIGHTS[phase].values())
            )[0]

            bedrooms = random.choice([2, 3, 3, 4]) if area_sqm >= 120 else random.choice([1, 2, 2, 3])

            distance_to_entrance_m = int(abs(i - LOTS_PER_BLOCK / 2) * 12 + block * 25 + random.randint(-10, 10))
            distance_to_entrance_m = max(distance_to_entrance_m, 15)

            launch = PHASE_LAUNCH_DATE[phase]
            days_since_launch = (TODAY - launch).days
            date_listed = launch + timedelta(days=random.randint(0, max(days_since_launch, 1)))

            date_reserved = None
            date_sold = None
            if status in ("reserved", "sold"):
                reserve_gap = random.randint(3, 45)
                date_reserved = date_listed + timedelta(days=reserve_gap)
                if date_reserved > TODAY:
                    date_reserved = TODAY
            if status == "sold":
                sell_gap = random.randint(5, 60)
                date_sold = date_reserved + timedelta(days=sell_gap)
                if date_sold > TODAY:
                    date_sold = TODAY

            lot = {
                "lot_id": lot_id,
                "block": block,
                "phase": phase,
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "area_sqm": area_sqm,
                "price_php": price_php,
                "price_per_sqm": round(price_php / area_sqm, 2),
                "status": status,
                "lot_type": lot_type,
                "bedrooms": bedrooms,
                "distance_to_entrance_m": distance_to_entrance_m,
                "date_listed": date_listed.isoformat(),
                "date_reserved": date_reserved.isoformat() if date_reserved else "",
                "date_sold": date_sold.isoformat() if date_sold else "",
            }
            lots.append(lot)

            # sales_log events
            agent = random.choice(["A. Reyes", "M. Santos", "J. Cruz", "K. Villanueva", "R. Dela Cruz"])
            sales_log.append({"lot_id": lot_id, "event": "listed", "event_date": date_listed.isoformat(), "agent": agent})
            if date_reserved:
                sales_log.append({"lot_id": lot_id, "event": "reserved", "event_date": date_reserved.isoformat(), "agent": agent})
            if date_sold:
                sales_log.append({"lot_id": lot_id, "event": "sold", "event_date": date_sold.isoformat(), "agent": agent})

            lot_counter += 1

# ---- Amenities (fictional POIs within the subdivision) ----
amenities = [
    {"name": "Main Entrance & Guardhouse", "type": "entrance", "lat": ANCHOR_LAT - 0.0004, "lng": ANCHOR_LNG + 0.0003},
    {"name": "Palm Ridge Clubhouse", "type": "clubhouse", "lat": ANCHOR_LAT + 0.0006, "lng": ANCHOR_LNG + 0.0008},
    {"name": "Community Pool", "type": "pool", "lat": ANCHOR_LAT + 0.0007, "lng": ANCHOR_LNG + 0.0009},
    {"name": "Ridge Park & Playground", "type": "park", "lat": ANCHOR_LAT + 0.0012, "lng": ANCHOR_LNG + 0.0004},
    {"name": "Palm Ridge Elementary Annex", "type": "school", "lat": ANCHOR_LAT + 0.0018, "lng": ANCHOR_LNG + 0.0002},
]

# ---- Write CSVs ----
with open(os.path.join(DATA_DIR, "lots.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=lots[0].keys())
    writer.writeheader()
    writer.writerows(lots)

with open(os.path.join(DATA_DIR, "amenities.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=amenities[0].keys())
    writer.writeheader()
    writer.writerows(amenities)

with open(os.path.join(DATA_DIR, "sales_log.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=sales_log[0].keys())
    writer.writeheader()
    writer.writerows(sales_log)

with open(os.path.join(DATA_DIR, "lots.json"), "w") as f:
    json.dump({"lots": lots, "amenities": amenities}, f, indent=2)

print(f"Generated {len(lots)} lots across {len(PHASES)} phases.")
print(f"Sales log entries: {len(sales_log)}")
status_counts = {}
for l in lots:
    status_counts[l["status"]] = status_counts.get(l["status"], 0) + 1
print("Status breakdown:", status_counts)
