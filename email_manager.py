import datetime
import logging
import pyshorteners

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

# Create one shortener instance (reused)
try:
    shortener = pyshorteners.Shortener(timeout=60)
except Exception as e:
    logging.warning(f"Failed to init TinyURL shortener: {e}")
    shortener = None

def build_emails(flight_deals):
    """
    flight_deals: list of deal dicts from data_manager.process_flight_deals()
    Returns dict: {email: email_body_string}
    """
    emails = {}
    if not flight_deals:
        logging.info("No flight deals to build emails for")
        return emails

    for flight in flight_deals:
        email = flight["user_email"]
        if email not in emails:
            emails[email] = (
                "Subject: Checkout your flight deals!\n"
                "MIME-Version: 1.0\n"
                "Content-Type: text/html; charset=utf-8\n\n"
                "<h2 style='color: #2c3e50;'>✈️ Flight Deals Found For You</h2>\n"
            )

        route = f'{flight["departure"]["name"]} → {flight["arrival"]["name"]}'

        # Format dates
        dep_dt = datetime.datetime.strptime(flight["departure"]["time"], "%Y-%m-%d %H:%M")
        arr_dt = datetime.datetime.strptime(flight["arrival"]["time"], "%Y-%m-%d %H:%M")
        dep_date_time = dep_dt.strftime("%d-%b-%Y %H:%M")
        arr_date_time = arr_dt.strftime("%d-%b-%Y %H:%M")

        # Layover HTML
        layover_text = ""
        if flight.get("layovers"):
            layover_text += "<p><strong>🛑 Layovers:</strong></p><ul style='list-style-type: none;'>"
            for layover in flight["layovers"]:
                arr_time = datetime.datetime.strptime(layover["arrival_time"], "%Y-%m-%d %H:%M")
                dep_time = datetime.datetime.strptime(layover["departure_time"], "%Y-%m-%d %H:%M")
                duration_hrs = round((dep_time - arr_time).total_seconds() / 3600, 1)
                layover_text += (
                    f"<li style='margin-bottom: 12px;'>"
                    f"&nbsp;&nbsp;Arrival: {arr_time.strftime('%H:%M')} <br>"
                    f"&nbsp;&nbsp;↓ <strong>{layover['airport']}</strong> (⏱ {duration_hrs} hrs) <br>"
                    f"&nbsp;&nbsp;Depart: {dep_time.strftime('%H:%M')} | "
                    f"<img src='{layover['airline_logo']}' width='20' height='20' style='vertical-align: middle; border-radius: 4px;'> "
                    f"<strong>{layover['airline']}</strong>"
                    f"</li>"
                )
            layover_text += "</ul>"
        else:
            layover_text = "<p>✈️ <strong>Direct Flight</strong></p>"

        # Shorten booking link (with fallback)
        booking_link = flight['booking_link']
        if shortener:
            try:
                booking_link = shortener.tinyurl.short(flight['booking_link'])
            except Exception as e:
                logging.warning(f"URL shortening failed for {flight['booking_link']}: {e}")

        emails[email] += f"""
        <hr style="border: 1px solid #eee;">
        <h4 style="margin-bottom: 5px;">→ Route: {route}</h4>
        <p><strong>{dep_date_time}</strong><br>
        🛫 <strong>Departure:</strong> {flight['departure']['name']}<br>
        <img src='{flight['airline_logo']}' width='20' height='20' style='vertical-align: middle; border-radius: 4px;'> 
        <strong>{flight['airline']}</strong>
        </p>
        {layover_text}
        <p>🛬 <strong>Arrival:</strong> {flight['arrival']['name']}<br>
        <strong>{arr_date_time}</strong></p>
        <p>💰 <strong>£{flight['price']}</strong> | ⏱ {round(flight['duration']/60, 1)} hrs</p>
        <p>🔗 <strong><a href='{booking_link}' style='color: #2980b9;'>Book Now</a></strong></p>
        <br>
        """
    return emails