import os
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import TOKEN_ENDPOINT, IATA_ENDPOINT, FLIGHT_ENDPOINT, MAX_FLIGHT_RESULTS, DEFAULT_CURRENCY
from flight_data import FlightData

load_dotenv(Path(__file__).parent.parent / ".env")


class FlightSearch:
    """Amadeus API client — IATA code lookup and flight offer search."""

    def __init__(self):
        self._api_key = os.environ["API_KEY_AMADEUS"]
        self._api_secret = os.environ["SECRET_AMADEUS"]
        self._token = self._get_new_token()

    def _get_new_token(self) -> str:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "client_credentials",
            "client_id": self._api_key,
            "client_secret": self._api_secret,
        }
        response = requests.post(url=TOKEN_ENDPOINT, headers=headers, data=body)
        response.raise_for_status()
        data = response.json()
        print(f"Token retrieved. Expires in {data.get('expires_in')} seconds.")
        return data["access_token"]

    def get_destination_code(self, city_name: str) -> str:
        """Return the IATA city code for a given city name, or 'N/A' if not found."""
        headers = {"Authorization": f"Bearer {self._token}"}
        params = {"keyword": city_name, "subType": "CITY"}
        response = requests.get(url=IATA_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        try:
            return response.json()["data"][0]["iataCode"]
        except (IndexError, KeyError):
            print(f"IATA code not found for {city_name}")
            return "N/A"

    def get_destination_codes(self, city_name: str) -> list[str]:
        """Return all IATA airport codes for a given city name."""
        headers = {"Authorization": f"Bearer {self._token}"}
        params = {"keyword": city_name, "subType": "AIRPORT"}
        response = requests.get(url=IATA_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        results = response.json().get("data", [])
        codes = [item["iataCode"] for item in results if "iataCode" in item]
        if not codes:
            print(f"No airport codes found for {city_name}")
        else:
            print(f"Found {len(codes)} airport(s) for {city_name}: {codes}")
        return codes

    def check_flights(
        self,
        origin_city_code: str,
        destination_city_code: str,
        from_time: datetime,
        to_time: datetime,
        is_direct: bool = True,
    ) -> tuple[list[FlightData] | None, list[dict] | None]:
        """
        Search Amadeus for round-trip flight offers.

        Returns (list[FlightData], None) on success or (None, list[error_dict]) on failure.
        """
        headers = {"Authorization": f"Bearer {self._token}"}
        query = {
            "originLocationCode": origin_city_code,
            "destinationLocationCode": destination_city_code,
            "departureDate": from_time.strftime("%Y-%m-%d"),
            "returnDate": to_time.strftime("%Y-%m-%d"),
            "adults": 1,
            "nonStop": str(is_direct).lower(),
            "currencyCode": os.getenv("CURRENCY", DEFAULT_CURRENCY),
            "max": MAX_FLIGHT_RESULTS,
        }

        response = requests.get(url=FLIGHT_ENDPOINT, headers=headers, params=query)

        if response.status_code != 200:
            return None, [{"status": response.status_code, "title": response.text}]

        data = response.json()
        if not data.get("data"):
            return None, data.get("errors", [{"status": response.status_code, "title": "No flights found"}])

        flights: list[FlightData] = []
        try:
            for offer in data["data"]:
                outbound = offer["itineraries"][0]["segments"]
                inbound = offer["itineraries"][1]["segments"]
                stop_overs = len(outbound) - 1
                via_city = [seg["arrival"]["iataCode"] for seg in outbound[:-1]] if stop_overs > 0 else []
                flights.append(
                    FlightData(
                        price=offer["price"]["grandTotal"],
                        origin_airport=outbound[0]["departure"]["iataCode"],
                        destination_airport=outbound[-1]["arrival"]["iataCode"],
                        out_date=outbound[0]["departure"]["at"].split("T")[0],
                        return_date=inbound[0]["departure"]["at"].split("T")[0],
                        stop_overs=stop_overs,
                        via_city=via_city,
                    )
                )
            return flights, None
        except (KeyError, IndexError) as e:
            return None, [{"status": response.status_code, "title": f"Error parsing flight data: {e}"}]
