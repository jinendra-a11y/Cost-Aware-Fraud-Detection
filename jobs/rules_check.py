import asyncio
from datetime import datetime
from typing import List, Dict
from .route_founder import get_route_distance # . for import from same folder
from .postalcode_to_lat_long import get_lat_long_from_postcode

# -----------------------------
# Helpers
# -----------------------------
ACCESS_TRAVEL_TYPES = {
    "Bus Ticket",
    "Train Ticket",
    "Metro Ticket",
    "Taxi Bill",
    "Other Expense"
}

def parse_dt(dt_str: Optional[str]):
    try:
        if not dt_str:
            return None

        dt = datetime.fromisoformat(dt_str)

        # Remove timezone if present
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        return dt

    except Exception:
        return None


def time_validation(bill: dict, job: dict):

    failed = []
    bill_type = bill.get("bill_type")
    bill_datetime_str = bill.get("bill_date_time")
    pickup_str = job.get("pickup_time")
    drop_str = job.get("drop_time")

    if not bill_datetime_str or not pickup_str or not drop_str:
        failed.append("INSUFFICIENT_DATA")
        return failed 

    # Parse ISO datetime
    bill_dt = parse_dt(bill_datetime_str)
    pickup_dt = parse_dt(pickup_str)
    drop_dt = parse_dt(drop_str)   

    # ----------------------------------------
    # ACCESS TRAVEL LOGIC
    # ----------------------------------------
    if bill_type in ACCESS_TRAVEL_TYPES:

        bill_date = bill_dt.date()
        pickup_date = pickup_dt.date()

        day_diff = abs((bill_date - pickup_date).days)

        if bill.get("amount") > 10:
            failed.append("BILL_AMOUNT_UNREASONABLE")

        if day_diff > 1:
           failed.append("ACCESS_TRAVEL_DATE_TOO_FAR")
        
        return failed

    # ----------------------------------------
    # STRICT BASE RULE (Non Access Travel)
    # ----------------------------------------
    else:
        if not (pickup_dt <= bill_dt <= drop_dt):
            failed.append("TIME_OUTSIDE_JOB_WINDOW")

    return failed


def check_bill_total(bill: dict, tolerance: float = 0.05):
    total = bill.get("amount")
    items = bill.get("line_items")

    if total is None:
        return "INSUFFICIENT_DATA"

    if not items or not isinstance(items, list):
        return None

    try:
        item_sum = sum(item.get("amount", 0) for item in items)
    except Exception:
        return "INSUFFICIENT_DATA"

    if abs(item_sum - total) > tolerance:
        return "BILL_TOTAL_MISMATCH"

    return None

def check_location_validation(bill: dict, pickup_latitude: float, pickup_longitude: float, drop_latitude: float, drop_longitude: float, distance_between_pickup_and_drop: int):
    distance_treshold_km = 30
    bill_location = bill.get("location_postal_code")
    
    bill_location_data = get_lat_long_from_postcode(bill_location)
    bill_latitude, bill_longitude = bill_location_data.get("latitude"), bill_location_data.get("longitude")

    distance_between_pickup_and_bill_location = get_route_distance(pickup_latitude, pickup_longitude, bill_latitude, bill_longitude).get("distance_km")
    distance_between_bill_location_and_drop = get_route_distance(bill_latitude, bill_longitude, drop_latitude, drop_longitude).get("distance_km")
    print(f"[DEBUG] Distances - Pickup to Drop: {distance_between_pickup_and_drop} km, Pickup to Bill: {distance_between_pickup_and_bill_location} km, Bill to Drop: {distance_between_bill_location_and_drop} km") 
    distances = [
    distance_between_pickup_and_drop,
    distance_between_pickup_and_bill_location,
    distance_between_bill_location_and_drop,
    ]

    if not all(isinstance(d, (int, float)) for d in distances):
        return None

    if distance_between_pickup_and_drop - (distance_between_pickup_and_bill_location + distance_between_bill_location_and_drop) > distance_treshold_km:
        return ["BILL_LOCATION_UNREASONABLE"]

    return None


# ------------------------
# Per-bill rule engine
# ------------------------
async def rule_engine_per_bill(
    bill: dict,
    job_details: dict,   # unused, kept for compatibility
    seen: dict,
    duplicates: list,
    pickup_latitude: float,
    pickup_longitude: float,
    drop_latitude: float,
    drop_longitude: float,
    distance_between_pickup_and_drop: float
) -> Dict:
    bill_id = bill.get("bill_id")
    failed = []

    # ------------------------
    # Mandatory fields check
    # ------------------------
    required = ["bill_type", "bill_date_time", "amount", "currency", "vendor", "location"]
    if any(field not in bill for field in required):
        failed.append("INSUFFICIENT_DATA")

    # ------------------------
    # Currency check
    # ------------------------
    if bill.get("currency") != "GBP":
        failed.append("BILL_CURRENCY_MISMATCH")

    # ------------------------
    # Amount sanity
    # ------------------------
    amount = bill.get("amount")

    if not isinstance(amount, (int, float)):
        failed.append("INSUFFICIENT_DATA")
    else:
        if amount <= 0:
            failed.append("BILL_AMOUNT_UNACCEPTABLE")


    # ------------------------
    # Duplicate check
    # ------------------------
    signature = (
        bill.get("bill_type"),
        bill.get("bill_date_time"),
        bill.get("amount"),
        bill.get("vendor"),
    )

    if signature in seen:
        duplicates.append(bill_id)
    else:
        seen[signature] = bill_id

        # ------------------------
        # Total check
        # ------------------------
        total_check = check_bill_total(bill)
        if total_check:
            failed.append(total_check)
        time_check = time_validation(bill, job_details)
        if time_check:
            failed.extend(time_check)
        if bill.get("bill_type") not in ACCESS_TRAVEL_TYPES:
            location_check = check_location_validation(bill, pickup_latitude, pickup_longitude, drop_latitude, drop_longitude, distance_between_pickup_and_drop)

            failed.append(location_check)

    return {
        "bill_id": bill_id,
        "fails": failed,
    }


# -----------------------------
# Batch rule engine
# -----------------------------
async def run_rule_engine(bills: List[dict], job_details: dict) -> dict:
    seen = {}
    duplicates = []
    tasks = []
    job_pickup_location = job_details.get("pickup_location")
    job_drop_location = job_details.get("drop_location")

    pickup_data = get_lat_long_from_postcode(job_pickup_location)
    drop_data = get_lat_long_from_postcode(job_drop_location)

    pickup_latitude, pickup_longitude = pickup_data.get("latitude"), pickup_data.get("longitude")
    drop_latitude, drop_longitude = drop_data.get("latitude"), drop_data.get("longitude")

    distance_between_pickup_and_drop = get_route_distance(pickup_latitude, pickup_longitude, drop_latitude, drop_longitude).get("distance_km")
    for bill in bills:
        result = rule_engine_per_bill(bill, job_details, seen, duplicates, pickup_latitude, pickup_longitude, drop_latitude, drop_longitude, distance_between_pickup_and_drop)
        if bill.get('bill_id') not in duplicates:
            tasks.append(result)
    
    results = await asyncio.gather(*tasks)

    per_bill = {r["bill_id"]: r["fails"] for r in results}

    for id in duplicates:
        per_bill[id] = ["DUPLICATE_BILL"]

    print("[DEBUG] per_bill:", per_bill)

    return {
        "per_bill": per_bill,
        "duplicates": duplicates,
    }
