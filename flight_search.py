import os
import requests
import datetime
from serpapi import GoogleSearch
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

SERP_API_KEY = os.getenv("SERP_API_KEY")
FORM_SHEETS_URL = os.getenv("SHEETS_URL_FORM_RESPONSES")   # Sheety endpoint for form responses
DELETE_FORM_ROW_URL = os.getenv("SHEETS_FLIGHT_DEAL_DELETE_URL") 

def delete_expired_form_row(target):
    """Delete the row in the form responses sheet that matches this expired target."""
    if not FORM_SHEETS_URL or not DELETE_FORM_ROW_URL:
        logging.warning("Form sheet URLs not configured – cannot delete expired rows")
        return False

    try:
        resp = requests.get(FORM_SHEETS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        rows = resp.json().get("formResponses2", [])
    except Exception as e:
        logging.error(f"Failed to fetch form responses: {e}")
        return False

    matching_row_id = None
    for row in rows:
        try:
            email_match = row.get("emailAddress", "").strip().lower() == target["user_email"].lower()
            dep_match = row.get("enterYourDepartureAirportCode. [resourceInDescription]", "").strip().upper() == target["departure_code"].upper()
            arr_match = row.get("enterYourArrivalAirportCode. [resourceInDescription]", "").strip().upper() == target["destination_code"].upper()
            form_date = datetime.datetime.strptime(row["specifyYourJourneyDate."], "%m/%d/%Y").strftime("%Y-%m-%d")
            date_match = form_date == target["departure_date"]

            if email_match and dep_match and arr_match and date_match:
                matching_row_id = row["id"]
                break
        except (KeyError, ValueError) as e:
            logging.debug(f"Skipping malformed form row: {e}")

    if matching_row_id:
        try:
            del_resp = requests.delete(f"{DELETE_FORM_ROW_URL}{matching_row_id}", timeout=10)
            if del_resp.status_code in (200, 204):
                logging.info(f"Deleted expired form row {matching_row_id} for {target['user_email']}")
                return True
            else:
                logging.warning(f"Failed to delete row {matching_row_id}: {del_resp.status_code}")
        except Exception as e:
            logging.error(f"Error deleting row {matching_row_id}: {e}")
    else:
        logging.warning(f"No matching form row found for expired target {target['user_email']}")
    return False

def search_single_target(target):
    """Search flights for one target. Returns (target_index, results_dict or None)."""
    today = datetime.datetime.today()
    try:
        departure_date = datetime.datetime.strptime(target["departure_date"], "%Y-%m-%d")
        if departure_date < today:
            logging.info(f"Expired flight for {target['user_email']} on {target['departure_date']} – deleting row")
            delete_expired_form_row(target)
            return None   # No results for expired target

        logging.info(f"SEARCHING | {target['departure_code']}→{target['destination_code']} | {target['departure_date']}")
        params = {
            "engine": "google_flights",
            "departure_id": target["departure_code"],
            "arrival_id": target["destination_code"],
            "outbound_date": target["departure_date"],
            "currency": "GBP",
            "hl": "en",
            "gl": "uk",
            "api_key": SERP_API_KEY,
            "type": "2"
        }
        search = GoogleSearch(params)
        result = search.get_dict()
        return result
    except Exception as e:
        logging.error(f"Error searching for {target['user_email']}: {e}")
        return None

def search_flights(targets):
    """Parallel search for all targets. Returns list of results (same order as targets)."""
    results = [None] * len(targets)
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_index = {executor.submit(search_single_target, target): idx for idx, target in enumerate(targets)}
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                res = future.result()
                results[idx] = res
            except Exception as e:
                logging.error(f"Search failed for target index {idx}: {e}")
                results[idx] = None
    return results