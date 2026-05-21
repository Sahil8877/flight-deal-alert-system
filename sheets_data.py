import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

SHEETS_URL = os.getenv('SHEETS_URL_FLIGHT_DEAL')
HEADERS = {"User-Agent": "Mozilla/5.0"}

def load_targets():
    """Fetch and parse flight deal targets from Google Sheet."""
    if not SHEETS_URL:
        logging.error("SHEETS_URL_FLIGHT_DEAL not set in environment")
        return []

    try:
        response = requests.get(SHEETS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data_json = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch sheet data: {e}")
        return []

    targets = []
    for row in data_json.get("sheet1", []):
        email = (row.get("emailAddress") or "").strip()
        if not email:
            logging.warning(f"Skipping row without email: {row.get('id')}")
            continue

        # Original price from form, and the 'lowestPriceFound' column (if any)
        original_price = row.get("priceTarget", float('inf'))
        lowest_found = row.get("lowestPriceFound")

        if lowest_found in (None, ""):
            current_target = float(original_price)
        else:
            current_target = float(lowest_found)

        targets.append({
            "destination_code": row["destinationCode"],
            "departure_code": row["departureCode"],
            "price_target": current_target,
            "duration_target": int(row["durationTarget"]),
            "layover_count": row["layoverCount"],
            "user_email": email,
            "departure_date": row["departureDate"],
            "row_id": row["id"],
        })

    logging.info(f"Loaded {len(targets)} valid targets from sheet")
    return targets