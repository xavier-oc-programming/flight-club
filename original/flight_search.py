"""
flight_search.py

This module provides the FlightSearch class for accessing the Amadeus Flight Offers and Location APIs.

Key responsibilities:
- Generate OAuth2 access token via Amadeus authentication endpoint.
- Query the city/location endpoint to fetch IATA city or airport codes from city names.
- Query the flight offers endpoint to search for flights based on origin, destination, and dates.

Environment Variables required in `.env`:
- API_KEY_AMADEUS: Your Amadeus API Key
- SECRET_AMADEUS: Your Amadeus API Secret
- CURRENCY: (optional) Currency code for prices (default: EUR)

Usage:
    from flight_search import FlightSearch
    fs = FlightSearch()
    flights, error = fs.check_flights("MAD", "NYC", from_time, to_time)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from flight_data import FlightData  

# Load credentials
load_dotenv()

# API Endpoints
TOKEN_ENDPOINT = "https://test.api.amadeus.com/v1/security/oauth2/token"
IATA_ENDPOINT = "https://test.api.amadeus.com/v1/reference-data/locations"
FLIGHT_ENDPOINT = "https://test.api.amadeus.com/v2/shopping/flight-offers"


class FlightSearch:
    """
    A class for querying the Amadeus API to retrieve IATA codes and flight offers.  

    This class handles authentication with Amadeus (via OAuth2), fetching IATA 
    city/airport codes, and searching for flight offers within a date range.  
    Returned flight data is parsed into `FlightData` objects.

    Attributes:
        _api_key (str): Amadeus API key, loaded from `.env`.
            Example: "your_amadeus_api_key_here"  # e.g. AB1cdEfg2hIJ3KL4MNopQR5stUvwXY6Z

        _api_secret (str): Amadeus API secret, loaded from `.env`.
            Example: "your_amadeus_secret_here"  # e.g. aB1cD2eF3gH4

        _token (str): Bearer token retrieved from the Amadeus authentication endpoint.
            Example: "eyJhbGciOiJIUzI1..."

    Methods:
        __init__():
            Initializes credentials and requests a new OAuth2 token from Amadeus.

        _get_new_token() -> str:
            Generate and return an OAuth2 access token using client credentials.

        get_destination_code(city_name: str) -> str:
            Return the IATA city code (3 letters) for a given city.
            Example: "London" -> "LON"

        get_destination_codes(city_name: str) -> List[str]:
            Return all airport codes for a given city.
            Example: "London" -> ["LHR", "LGW", "STN", "LCY", "LTN"]

        check_flights(
            origin_city_code: str,
            destination_city_code: str,
            from_time: datetime,
            to_time: datetime,
            is_direct: bool = True
        ) -> tuple[list[FlightData] | None, list[dict] | None]:
            Query the Amadeus flight offers endpoint for available flights.  
            Returns a tuple:
                - (list of FlightData, None) on success
                - (None, list of error dicts) if request fails or no flights are found

    Example:
        >>> from datetime import datetime, timedelta
        >>> fs = FlightSearch()
        >>> city_code = fs.get_destination_code("New York")
        'NYC'
        >>> airports = fs.get_destination_codes("London")
        ['LHR', 'LGW', 'STN', 'LCY', 'LTN']
        >>> flights, error = fs.check_flights(
        ...     "MAD", "NYC",
        ...     datetime.now() + timedelta(days=10),
        ...     datetime.now() + timedelta(days=17),
        ...     is_direct=True
        ... )
        >>> if flights:
        ...     for f in flights:
        ...         print(f.as_string())
        MAD -> JFK = 450.99 EUR [2025-11-01 TO 2025-11-08] (Round Trip)
    """


    def __init__(self):
        self._api_key = os.environ["API_KEY_AMADEUS"]
        self._api_secret = os.environ["SECRET_AMADEUS"]
        self._token = self._get_new_token()

    def _get_new_token(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "client_credentials",
            "client_id": self._api_key,
            "client_secret": self._api_secret
        }
        response = requests.post(url=TOKEN_ENDPOINT, headers=headers, data=body)
        response.raise_for_status()
        token = response.json()["access_token"]
        print(f"✅ Token retrieved. Expires in {response.json().get('expires_in')} seconds.")
        return token

    def get_destination_code(self, city_name):
        """
        Returns the IATA city code for a given city (if available).
        Example: "London" -> "LON"
        """
        headers = {"Authorization": f"Bearer {self._token}"}
        params = {"keyword": city_name, "subType": "CITY"}

        response = requests.get(url=IATA_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()

        try:
            return response.json()["data"][0]["iataCode"]
        except (IndexError, KeyError):
            print(f"⚠️ IATA code not found for {city_name}")
            return "N/A"

    def get_destination_codes(self, city_name):
        """
        Returns all IATA airport codes belonging to a city.
        Example: "London" -> ["LHR", "LGW", "STN", "LCY", "LTN"]
        """
        headers = {"Authorization": f"Bearer {self._token}"}
        params = {"keyword": city_name, "subType": "AIRPORT"}

        response = requests.get(url=IATA_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()

        results = response.json().get("data", [])
        codes = [item["iataCode"] for item in results if "iataCode" in item]

        if not codes:
            print(f"⚠️ No airport codes found for {city_name}")
        else:
            print(f"✅ Found {len(codes)} airport(s) for {city_name}: {codes}")

        return codes

    def check_flights(self, origin_city_code, destination_city_code, from_time, to_time, is_direct=True):
        """
        Queries Amadeus to search for available flight offers between two cities/airports.

        Parameters:
            origin_city_code (str): IATA code of the origin city/airport.
            destination_city_code (str): IATA code of the destination city/airport.
            from_time (datetime): Earliest departure date.
            to_time (datetime): Latest return date.
            is_direct (bool): Whether to restrict search to direct flights only.

        Returns:
            tuple: (list[FlightData], None) if success,
                   (None, error_list) if no data or error.
        """
        headers = {"Authorization": f"Bearer {self._token}"}
        query = {
            "originLocationCode": origin_city_code,
            "destinationLocationCode": destination_city_code,
            "departureDate": from_time.strftime("%Y-%m-%d"),
            "returnDate": to_time.strftime("%Y-%m-%d"),
            "adults": 1,
            "nonStop": str(is_direct).lower(),
            "currencyCode": os.getenv("CURRENCY", "EUR"),
            "max": 5
        }

        response = requests.get(url=FLIGHT_ENDPOINT, headers=headers, params=query)

        if response.status_code != 200:
            return None, [{"status": response.status_code, "title": response.text}]

        data = response.json()
        if not data.get("data"):
            return None, data.get("errors", [{
                "status": response.status_code,
                "title": "No flights found"
            }])

        flights = []
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
                        via_city=via_city
                    )
                )

            return flights, None
        except (KeyError, IndexError) as e:
            return None, [{"status": response.status_code, "title": f"Error parsing flight data: {e}"}]


# ============================
# Optional Test Block
# ============================
if __name__ == "__main__":
    from datetime import timedelta

    print("\n==============================")
    print("🧪 TEST: FlightSearch Module")
    print("==============================\n")

    fs = FlightSearch()

    # --- IATA Lookup Test ---
    print("🔎 Testing IATA Code Lookup")
    cities = ["Madrid", "New York", "Tokyo", "London", "Kuala Lumpur"]
    for city in cities:
        try:
            city_code = fs.get_destination_code(city)
            airport_codes = fs.get_destination_codes(city)
            print(f"{city} → City Code: {city_code}, Airports: {airport_codes}")
        except requests.exceptions.HTTPError as e:
            print(f"❌ Failed to fetch IATA info for {city} - {e}")

    # --- Flight Search Test ---
    print("\n🛫 Testing Flight Offer Search")

    origin = "MAD"
    destination = "LHR"  # London Heathrow
    from_date = datetime.now() + timedelta(days=20)
    to_date = datetime.now() + timedelta(days=27)

    flights, error = fs.check_flights(origin, destination, from_date, to_date, is_direct=False)

    if flights:
        print("✅ Flights found:")
        for f in flights:
            print(f"   - {f.as_string()}")
    else:
        print("⚠️ No flight data returned.")
        for err in error:
            status = err.get("status", "N/A")
            title = err.get("title", "Unknown response")
            print(f"   ↳ Status code {status}: {title}")
