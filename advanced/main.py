import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from config import (
    ORIGIN_CITY_IATA,
    SEARCH_WINDOW_DAYS,
    IATA_LOOKUP_DELAY,
    DEFAULT_CURRENCY,
    EMAIL_SUBJECT,
    SMTP_SERVER_DEFAULT,
    SMTP_PORT_DEFAULT,
)
from flight_data import FlightData, find_cheapest_flight
from flight_search import FlightSearch
from data_manager import DataManager
from notifier import Notifier


def main() -> None:
    data_manager = DataManager()
    flight_search = FlightSearch()
    notifier = Notifier(
        email_subject=EMAIL_SUBJECT,
        smtp_server=SMTP_SERVER_DEFAULT,
        smtp_port=SMTP_PORT_DEFAULT,
    )

    # ── Step 1: Load destinations, fill any missing IATA codes ──────────────
    sheet_data = data_manager.get_destination_data()

    for row in sheet_data:
        if row["iataCode"] == "":
            print(f"Fetching IATA code for {row['city']}...")
            row["iataCode"] = flight_search.get_destination_code(row["city"])
            time.sleep(IATA_LOOKUP_DELAY)

    data_manager.destination_data = sheet_data
    data_manager.update_destination_codes()

    # ── Step 2: Search flights for each destination ──────────────────────────
    print(f"\nSearching round-trip flights from {ORIGIN_CITY_IATA}...\n")

    tomorrow = datetime.now() + timedelta(days=1)
    search_end = datetime.now() + timedelta(days=SEARCH_WINDOW_DAYS)

    for destination in sheet_data:
        code = destination["iataCode"]
        city_name = destination["city"]
        threshold = destination["lowestPrice"]

        if code == "N/A":
            print(f"No IATA city code for {city_name}. Trying airport codes...")
            airport_codes = flight_search.get_destination_codes(city_name)
            if not airport_codes:
                print(f"Skipping {city_name} (no airports found).")
                continue
        else:
            airport_codes = [code]

        for airport_code in airport_codes:
            print(f"Checking flights to {city_name} ({airport_code})...")

            flights, error = flight_search.check_flights(
                origin_city_code=ORIGIN_CITY_IATA,
                destination_city_code=airport_code,
                from_time=tomorrow,
                to_time=search_end,
                is_direct=True,
            )

            if not flights:
                print("No direct flights. Retrying with stopovers...")
                flights, error = flight_search.check_flights(
                    origin_city_code=ORIGIN_CITY_IATA,
                    destination_city_code=airport_code,
                    from_time=tomorrow,
                    to_time=search_end,
                    is_direct=False,
                )

            if not flights:
                print("No valid flight data.")
                if error:
                    for err in error:
                        print(f"  Status {err.get('status', 'N/A')}: {err.get('title', 'Unknown')}")
                continue

            print("Found flight options:")
            for f in flights:
                print(f"  {f.as_string()}")

            cheapest: FlightData = find_cheapest_flight(flights)

            if cheapest.price is None:
                print("No valid price data after parsing.")
                continue

            print(f"\nCheapest: {cheapest.as_string()}")
            print(f"Threshold: {threshold} {DEFAULT_CURRENCY}")

            # ── Step 3: Notify if price beats threshold ──────────────────────
            if cheapest.price < threshold:
                print("Price below threshold — sending notifications...")
                message = f"Flight Deal Alert!\n{cheapest.as_string()}"

                try:
                    notifier.send_sms(message)
                except Exception as e:
                    print(f"SMS failed: {e}")

                try:
                    customers = data_manager.get_customer_emails()
                    emails = [c["email"] for c in customers if c["email"]]
                    notifier.send_emails(message, emails)
                except Exception as e:
                    print(f"Email failed: {e}")
            else:
                print("Price above threshold — no notifications sent.")


if __name__ == "__main__":
    main()
