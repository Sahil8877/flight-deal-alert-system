import logging
import urllib.parse
import requests
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

def update_lowest_price_in_sheet(row_id, new_price):
    """Update the lowestPriceFound column in the flight deals sheet."""
    base_url = os.getenv('SHEETS_URL_FLIGHT_DEAL')
    if not base_url:
        logging.error("SHEETS_URL_FLIGHT_DEAL not set")
        return
    update_url = f"{base_url}/{row_id}"
    payload = {"sheet1": {"lowestPriceFound": new_price}}
    try:
        response = requests.put(update_url, json=payload, timeout=10)
        if response.status_code == 200:
            logging.info(f"✅ Sheet Updated! Row {row_id} new lowest price £{new_price}")
        else:
            logging.warning(f"Failed to update sheet: {response.text}")
    except Exception as e:
        logging.error(f"Error updating sheet price: {e}")

def process_flight_deals(targets, search_results):
    """
    Filter and structure flight deals.
    targets: list of target dicts (from sheets_data.load_targets())
    search_results: list of SerpAPI result dicts (parallel to targets)
    Returns list of structured flight deal dicts.
    """
    flight_deals = []

    for idx, target in enumerate(targets):
        if idx >= len(search_results) or not search_results[idx]:
            continue

        result = search_results[idx]
        flight_options = result.get('best_flights', []) or result.get('other_flights', [])
        search_date = result.get('search_parameters', {}).get('outbound_date', 'Unknown')

        if not flight_options:
            logging.info(f"NO FLIGHTS | {target['user_email']} | {target['departure_code']}→{target['destination_code']} | {search_date}")
            continue

        # Sort by price (cheapest first) to ensure we pick the best
        flight_options.sort(key=lambda x: x.get('price', float('inf')))

        for flight in flight_options:
            segments = flight.get('flights', [])
            if not segments:
                continue

            price = flight.get('price')
            total_duration = flight.get('total_duration', float('inf'))
            layover_count = max(len(segments) - 1, 0)

            if price is None:
                continue

            # Log all found flights
            logging.info(
                f"FOUND | {target['user_email']} | {segments[0]['departure_airport']['id']}→{segments[-1]['arrival_airport']['id']} | {search_date} | "
                f"£{price} | {total_duration}min | {layover_count} stops"
            )

            # Check constraints
            if (price <= target['price_target'] and
                total_duration <= target['duration_target'] and
                layover_count <= target['layover_count']):

                logging.info(f"ACCEPTED | {target['user_email']} | £{price}")

                # Update sheet if new price is strictly lower
                if price < target['price_target']:
                    update_lowest_price_in_sheet(target['row_id'], price)

                # Build layover details
                layovers = []
                for i, layover in enumerate(flight.get('layovers', [])):
                    if i + 1 < len(segments):
                        layovers.append({
                            "airport": layover.get('name'),
                            "arrival_time": segments[i]['arrival_airport'].get('time'),
                            "departure_time": segments[i+1]['departure_airport'].get('time'),
                            "duration": round(float(layover.get('duration', 0)) / 60, 1),
                            "airline": segments[i+1].get('airline', 'Unknown'),
                            "airline_logo": segments[i+1].get('airline_logo', '')
                        })

                # Booking link
                query = f"Flights from {target['departure_code']} to {target['destination_code']} on {search_date} one way"
                encoded_query = urllib.parse.quote(query)
                booking_link = f"https://www.google.com/travel/flights?q={encoded_query}"

                flight_deals.append({
                    "departure": segments[0]['departure_airport'],
                    "airline": segments[0].get('airline', 'Unknown'),
                    "airline_logo": segments[0].get('airline_logo', ''),
                    "layovers": layovers,
                    "arrival": segments[-1]['arrival_airport'],
                    "price": price,
                    "duration": total_duration,
                    "booking_link": booking_link,
                    "booking_token": flight.get('booking_token'),
                    "user_email": target['user_email'],
                    "layover_count": layover_count
                })


    # Sort globally by price
    flight_deals.sort(key=lambda x: x['price'])
    logging.info(f"Total flight deals found: {len(flight_deals)}")
    return flight_deals