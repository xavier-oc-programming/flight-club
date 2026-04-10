"""
flight_search.py

This module provides the FlightSearch class for accessing the Google Flights API via SerpApi.

Key responsibilities:
- Search for round-trip flight offers based on origin, destination, and date range.

Note: SerpApi does not provide an IATA lookup endpoint. Airport codes must be
set directly in the Google Sheet before running.

Environment Variables required in `.env`:
- SERPAPI_KEY: Your SerpApi API key
- CURRENCY: (optional) Currency code for prices (default: EUR)

Usage:
    from flight_search import FlightSearch
    fs = FlightSearch()
    flights, error = fs.check_flights("MAD", "NYC", from_time, to_time)
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flight_data import FlightData

sys.path.insert(0, str(Path(__file__).parent))

# Load credentials
load_dotenv(Path(__file__).parent.parent / ".env")

SERPAPI_ENDPOINT = "https://serpapi.com/search"


class FlightSearch:
    """
    A class for querying Google Flights via SerpApi to retrieve flight offers.

    Attributes:
        _api_key (str): SerpApi key, loaded from `.env`.

    Methods:
        get_destination_code(city_name) -> str:
            Not supported — returns 'N/A'. Add codes directly to the sheet.

        get_destination_codes(city_name) -> List[str]:
            Not supported — returns []. Add codes directly to the sheet.

        check_flights(origin, destination, from_time, to_time, is_direct) -> tuple:
            Search Google Flights for round-trip offers departing on a specific date.
            Returns (list[FlightData], None) on success or (None, error_list) on failure.
    """

    def __init__(self):
        self._api_key = os.environ["SERPAPI_KEY"]

    def get_destination_code(self, city_name):
        """Not supported with SerpApi — returns 'N/A'."""
        print(f"⚠️ IATA lookup not supported. Add code for {city_name} directly to the sheet.")
        return "N/A"

    def get_destination_codes(self, city_name):
        """Not supported with SerpApi — returns []."""
        return []

    def check_flights(self, origin_city_code, destination_city_code, from_time, to_time, is_direct=True):
        """
        Search Google Flights via SerpApi for round-trip offers.

        Parameters:
            origin_city_code (str): IATA code of origin airport.
            destination_city_code (str): IATA code of destination airport.
            from_time (datetime): Outbound departure date.
            to_time (datetime): Return departure date.
            is_direct (bool): If True, restrict to non-stop flights only.

        Returns:
            tuple: (list[FlightData], None) if success,
                   (None, error_list) if no data or error.
        """
        params = {
            "engine": "google_flights",
            "departure_id": origin_city_code,
            "arrival_id": destination_city_code,
            "outbound_date": from_time.strftime("%Y-%m-%d"),
            "return_date": to_time.strftime("%Y-%m-%d"),
            "type": "1",  # round trip
            "adults": 1,
            "currency": os.getenv("CURRENCY", "EUR"),
            "api_key": self._api_key,
        }
        if is_direct:
            params["stops"] = "0"

        response = requests.get(url=SERPAPI_ENDPOINT, params=params)

        if response.status_code != 200:
            return None, [{"status": response.status_code, "title": response.text}]

        data = response.json()
        all_offers = data.get("best_flights", []) + data.get("other_flights", [])

        if not all_offers:
            return None, [{"status": 200, "title": "No flights found"}]

        flights = []
        try:
            for offer in all_offers[:5]:
                flight_legs = offer.get("flights", [])
                layovers = offer.get("layovers", [])

                origin = flight_legs[0]["departure_airport"]["id"] if flight_legs else origin_city_code
                destination = flight_legs[-1]["arrival_airport"]["id"] if flight_legs else destination_city_code
                out_date = flight_legs[0]["departure_airport"]["time"].split(" ")[0] if flight_legs else "N/A"
                return_date = params["return_date"]

                stop_overs = len(layovers)
                via_city = [lay["id"] for lay in layovers]

                flights.append(
                    FlightData(
                        price=offer["price"],
                        origin_airport=origin,
                        destination_airport=destination,
                        out_date=out_date,
                        return_date=return_date,
                        stop_overs=stop_overs,
                        via_city=via_city,
                    )
                )
            return flights, None
        except (KeyError, IndexError) as e:
            return None, [{"status": 200, "title": f"Error parsing flight data: {e}"}]


# ============================
# Optional Test Block
# ============================
if __name__ == "__main__":
    from datetime import timedelta

    print("\n==============================")
    print("🧪 TEST: FlightSearch Module (SerpApi)")
    print("==============================\n")

    fs = FlightSearch()

    print("🛫 Testing Flight Offer Search")
    flights, error = fs.check_flights(
        "MAD", "LHR",
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=180),
        is_direct=False
    )

    if flights:
        print("✅ Flights found:")
        for f in flights:
            print(f"   - {f.as_string()}")
    else:
        print("⚠️ No flight data returned.")
        for err in error:
            print(f"   ↳ {err.get('status')}: {err.get('title')}")
