import smtplib
import os
import logging
from sheets_data import load_targets
from flight_search import search_flights
from data_manager import process_flight_deals
from email_manager import build_emails

# Configure logging once
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_EMAIL_PASS')

def send_emails(emails_dict):
    """Send emails via Gmail SMTP."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logging.error("Sender email credentials missing – cannot send emails")
        return

    if not emails_dict:
        logging.info("No emails to send")
        return

    try:
        with smtplib.SMTP(host='smtp.gmail.com', timeout=30) as conn:
            conn.starttls()
            conn.login(user=SENDER_EMAIL, password=SENDER_PASSWORD)
            for recipient, msg_body in emails_dict.items():
                conn.sendmail(
                    from_addr=SENDER_EMAIL,
                    to_addrs=recipient,
                    msg=msg_body.encode("utf-8")
                )
                logging.info(f"ALERTED | user={recipient}")
    except Exception as e:
        logging.error(f"Failed to send emails: {e}")

def main():
    logging.info("Starting flight deal alert system")
    
    # 1. Load targets from sheet
    targets = load_targets()
    if not targets:
        logging.warning("No valid targets found – exiting")
        return

    # 2. Search flights (parallel)
    logging.info(f"Searching flights for {len(targets)} targets")
    search_results = search_flights(targets)

    # 3. Process deals (filter, update sheet)
    deals = process_flight_deals(targets, search_results)

    # 4. Build email HTML
    emails = build_emails(deals)

    # 5. Send emails
    send_emails(emails)

    logging.info("Flight deal alert system finished")

if __name__ == "__main__":
    main()