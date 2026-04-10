"""
main.py

Main script to automate flight deal discovery:
1. Fetch destination data from a Google Sheet via Sheety API.
2. Ensure each destination has a valid IATA code (via Amadeus API).
3. Search for flight offers from a fixed origin to each destination.
4. If no direct flights exist, retry with stopovers allowed.
5. Print all found offers, pick the cheapest, and notify user if it’s below the threshold.

Dependencies:
- data_manager.py
- flight_search.py
- flight_data.py
- notification_manager.py
- .env file with Sheety, Amadeus, Twilio, and Email credentials.
"""

import time
from datetime import datetime, timedelta
from data_manager import DataManager
from flight_search import FlightSearch
from flight_data import find_cheapest_flight, FlightData
from notification_manager import NotificationManager

# ============================
# Step 1: Initialize Managers
# ============================

data_manager = DataManager()
sheet_data = data_manager.get_destination_data()
flight_search = FlightSearch()
notifier = NotificationManager()

# ============================
# Step 2: Update Missing IATA Codes
# ============================

for row in sheet_data:
    if row["iataCode"] == "":
        print(f"\n🔍 Fetching IATA code for {row['city']}...")
        row["iataCode"] = flight_search.get_destination_code(row["city"])
        time.sleep(1.5)  # Avoid rate limit

# Save updated data back to sheet
data_manager.destination_data = sheet_data
data_manager.update_destination_codes()

# ============================
# Step 3: Search for Flights
# ============================

print("\n✈️ Searching for round-trip flights from MAD...\n")
ORIGIN_CITY_IATA = "MAD"

tomorrow = datetime.now() + timedelta(days=1)
six_months_later = datetime.now() + timedelta(days=180)

for destination in sheet_data:
    code = destination["iataCode"]
    city_name = destination["city"]
    threshold_price = destination["lowestPrice"]

    # --- Part 1: Check for valid IATA codes ---
    if code == "N/A":
        print(f"\n⚠️ No IATA city code for {city_name}. Trying airport codes instead...")
        airport_codes = flight_search.get_destination_codes(city_name)

        if not airport_codes:
            print(f"❌ Skipping {city_name} (no airports found).")
            continue
    else:
        airport_codes = [code]

    # --- Part 2: Loop through airport codes ---
    for airport_code in airport_codes:
        print(f"\n🔎 Checking flights to {city_name} ({airport_code})...")

        # First try direct flights
        flights, error = flight_search.check_flights(
            origin_city_code=ORIGIN_CITY_IATA,
            destination_city_code=airport_code,
            from_time=tomorrow,
            to_time=six_months_later,
            is_direct=True
        )

        # Retry with stopovers if none
        if not flights:
            print("⚠️ No direct flights found. Retrying with stopovers allowed...")
            flights, error = flight_search.check_flights(
                origin_city_code=ORIGIN_CITY_IATA,
                destination_city_code=airport_code,
                from_time=tomorrow,
                to_time=six_months_later,
                is_direct=False
            )

        # --- Still nothing → skip to next city ---
        if not flights:
            print("❌ No valid flight data available.")
            if error:
                for err in error:
                    status = err.get("status", "N/A")
                    title = err.get("title", "Unknown response")
                    print(f"   ↳ Status code {status}: {title}")
            continue

        # --- Part 3: Print all found flights ---
        print("📋 Found flight options:")
        for f in flights:
            print(f"   - {f.as_string()}")

        # --- Part 4: Pick cheapest flight ---
        cheapest_flight: FlightData = find_cheapest_flight(flights)

        if cheapest_flight.price is None:
            print("❌ No valid flight data available after parsing.")
            continue

        print("\n✅ Cheapest Flight Selected:")
        print(cheapest_flight.as_string())
        print(f"🔎 Evaluating if it is below marked threshold ({threshold_price})...")

        # --- Part 5: Notify if below threshold ---
        if cheapest_flight.price < threshold_price:
            print("📣 Price is below threshold! Sending notifications...")
            notifier.send_sms(cheapest_flight)      # ✅ Send SMS
            notifier.send_emails(cheapest_flight)   # ✅ Send to all Sheety users
        else:
            print(f"ℹ️ Price is above threshold ({threshold_price}). No notifications sent.")
