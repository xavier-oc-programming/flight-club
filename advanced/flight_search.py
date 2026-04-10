import os
import requests
from datetime import datetime
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import SERPAPI_ENDPOINT, MAX_FLIGHT_RESULTS, DEFAULT_CURRENCY
from flight_data import FlightData

load_dotenv(Path(__file__).parent.parent / ".env")


class FlightSearch:
    """SerpApi Google Flights client — flight offer search."""

    def __init__(self):
        self._api_key = os.environ["SERPAPI_KEY"]

    def get_destination_code(self, city_name: str) -> str:
        """Not used with SerpApi — airport codes must be set directly in the sheet."""
        return "N/A"

    def get_destination_codes(self, city_name: str) -> list[str]:
        """Not used with SerpApi — airport codes must be set directly in the sheet."""
        return []

    def check_flights(
        self,
        origin_city_code: str,
        destination_city_code: str,
        from_time: datetime,
        to_time: datetime,
        is_direct: bool = True,
    ) -> tuple[list[FlightData] | None, list[dict] | None]:
        """
        Search Google Flights via SerpApi for round-trip offers.

        Returns (list[FlightData], None) on success or (None, list[error_dict]) on failure.
        """
        params = {
            "engine": "google_flights",
            "departure_id": origin_city_code,
            "arrival_id": destination_city_code,
            "outbound_date": from_time.strftime("%Y-%m-%d"),
            "return_date": to_time.strftime("%Y-%m-%d"),
            "type": "1",  # round trip
            "adults": 1,
            "currency": os.getenv("CURRENCY", DEFAULT_CURRENCY),
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

        flights: list[FlightData] = []
        try:
            for offer in all_offers[:MAX_FLIGHT_RESULTS]:
                flight_legs = offer.get("flights", [])
                layovers = offer.get("layovers", [])

                origin = flight_legs[0]["departure_airport"]["id"] if flight_legs else origin_city_code
                destination = flight_legs[-1]["arrival_airport"]["id"] if flight_legs else destination_city_code
                out_date = flight_legs[0]["departure_airport"]["time"].split(" ")[0] if flight_legs else "N/A"

                # return date: taken from search params (SerpApi doesn't embed it in the offer)
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
