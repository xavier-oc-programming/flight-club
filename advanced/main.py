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

SEP = "─" * 50


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

    needs_update = [row for row in sheet_data if row["iataCode"] == ""]
    if needs_update:
        print("Syncing IATA codes...")
        for row in needs_update:
            row["iataCode"] = flight_search.get_destination_code(row["city"])
            time.sleep(IATA_LOOKUP_DELAY)
        data_manager.destination_data = sheet_data
        data_manager.update_destination_codes()
        print()

    # ── Step 2: Search flights for each destination ──────────────────────────
    tomorrow = datetime.now() + timedelta(days=1)
    search_end = datetime.now() + timedelta(days=SEARCH_WINDOW_DAYS)

    print(f"\nScanning flights from {ORIGIN_CITY_IATA}\n")

    for destination in sheet_data:
        code = destination["iataCode"]
        city_name = destination["city"]
        threshold = destination["lowestPrice"]

        print(f"\n{SEP}\n{city_name} ({code})")

        if code == "N/A":
            airport_codes = flight_search.get_destination_codes(city_name)
            if not airport_codes:
                print("  No airports found — skipped.")
                continue
        else:
            airport_codes = [code]

        for airport_code in airport_codes:
            flights, _ = flight_search.check_flights(
                origin_city_code=ORIGIN_CITY_IATA,
                destination_city_code=airport_code,
                from_time=tomorrow,
                to_time=search_end,
                is_direct=True,
            )

            if not flights:
                flights, _ = flight_search.check_flights(
                    origin_city_code=ORIGIN_CITY_IATA,
                    destination_city_code=airport_code,
                    from_time=tomorrow,
                    to_time=search_end,
                    is_direct=False,
                )

            if not flights:
                print("  No flights found.")
                continue

            for f in flights:
                print(f"  {f.as_string()}")

            cheapest: FlightData = find_cheapest_flight(flights)

            if cheapest.price is None:
                print("  Could not determine cheapest flight.")
                continue

            print(f"\n  Cheapest : {cheapest.price} {DEFAULT_CURRENCY}")
            print(f"  Threshold: {threshold} {DEFAULT_CURRENCY}")

            # ── Step 3: Notify if price beats threshold ──────────────────────
            if cheapest.price < threshold:
                print(f"  Deal found! {cheapest.price} {DEFAULT_CURRENCY} is under your {threshold} {DEFAULT_CURRENCY} target.")
                message = (
                    f"✈️ Flight Deal Alert!\n\n"
                    f"{ORIGIN_CITY_IATA} → {airport_code} ({city_name})\n"
                    f"Price:  {cheapest.price} {DEFAULT_CURRENCY}\n"
                    f"Depart: {cheapest.out_date}\n"
                    f"Return: {cheapest.return_date}\n"
                    f"Stops:  {cheapest.stop_overs}"
                )

                try:
                    notifier.send_whatsapp(message)
                    print("  WhatsApp ✓")
                except Exception as e:
                    print(f"  WhatsApp failed: {e}")

                try:
                    customers = data_manager.get_customer_emails()
                    emails = [c["email"] for c in customers if c["email"]]
                    notifier.send_emails(message, emails)
                    print(f"  Email ✓  ({len(emails)} recipient(s))")
                except Exception as e:
                    print(f"  Email failed: {e}")
            else:
                print(f"  No deal — {cheapest.price} {DEFAULT_CURRENCY} is above the {threshold} {DEFAULT_CURRENCY} target.")

    print(f"\n{SEP}\nDone.")


if __name__ == "__main__":
    main()
