"""
flight_data.py

This module defines the FlightData class, a structured container for flight deal information,
and a helper function `find_cheapest_flight()` which selects the cheapest option
from a list of flights.

Key functionalities:
- Store price, origin/destination IATA codes, and travel dates for a flight.
- Provide clean string and dict representations of flight details.
- Select the cheapest option from a list of FlightData objects.

Usage:
    from flight_data import FlightData, find_cheapest_flight

    flights = [
        FlightData(price=320.50, origin_airport="MAD", destination_airport="PAR",
                   out_date="2025-10-15", return_date="2025-10-20", origin_city="Madrid", destination_city="Paris"),
        FlightData(price=245.99, origin_airport="MAD", destination_airport="PAR",
                   out_date="2025-10-15", return_date="2025-10-20", stop_overs=1, via_city=["BCN"],
                   origin_city="Madrid", destination_city="Paris")
    ]
    cheapest = find_cheapest_flight(flights)
    print(cheapest.as_string())
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FlightData:
    """
    A class representing a single flight offer.

    Attributes:
        price (Optional[float]): Price of the flight. None if invalid.
        origin_airport (str): IATA code of the origin airport. Example: "MAD"
        destination_airport (str): IATA code of the destination airport. Example: "JFK"
        out_date (str): Outbound flight date (YYYY-MM-DD).
        return_date (str): Return flight date (YYYY-MM-DD).
        currency (str): Currency of the price. Defaults to "EUR".
        trip_type (str): Type of trip, "round" or "oneway".
        stop_overs (int): Number of stopovers. Example: 2.
        via_city (List[str]): List of IATA codes of stopover cities. Example: ["LIS", "AMS"].
        origin_city (Optional[str]): Human-readable origin city name. Example: "Madrid".
        destination_city (Optional[str]): Human-readable destination city name. Example: "New York".

    Methods:
        __init__(...):
            Initialize a FlightData object with the given attributes.

        to_dict() -> Dict[str, Any]:
            Return the flight data as a dictionary.

        as_string() -> str:
            Return a compact human-readable string of the flight details.

    Related Functions:
        find_cheapest_flight(flight_list: List[FlightData]) -> FlightData:
            Select and return the cheapest flight from a list of FlightData objects.

    Example:
        >>> flight = FlightData(
        ...     price=199.99,
        ...     origin_airport="MAD",
        ...     destination_airport="CDG",
        ...     out_date="2025-11-01",
        ...     return_date="2025-11-10",
        ...     stop_overs=1,
        ...     via_city=["BCN"],
        ...     origin_city="Madrid",
        ...     destination_city="Paris"
        ... )
        >>> flight.as_string()
        'MAD (Madrid) -> CDG (Paris) = 199.99 EUR [2025-11-01 TO 2025-11-10] (Round Trip) | Stops: 1 via BCN'
    """

    def __init__(
        self,
        price: Optional[float],
        origin_airport: str,
        destination_airport: str,
        out_date: str,
        return_date: str,
        currency: str = os.getenv("CURRENCY", "EUR"),
        trip_type: str = "round",
        stop_overs: int = 0,
        via_city: Optional[List[str]] = None,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None
    ) -> None:
        """Initialize a FlightData object with given attributes."""
        self.price: Optional[float] = float(price) if price not in (None, "N/A") else None
        self.origin_airport: str = origin_airport
        self.destination_airport: str = destination_airport
        self.out_date: str = out_date
        self.return_date: str = return_date
        self.currency: str = currency
        self.trip_type: str = trip_type.lower()
        self.stop_overs: int = stop_overs
        self.via_city: List[str] = via_city if via_city else []
        self.origin_city: Optional[str] = origin_city
        self.destination_city: Optional[str] = destination_city

    def to_dict(self) -> Dict[str, Any]:
        """
        Return the flight data as a dictionary.

        Example:
            >>> flight.to_dict()
            {
                'price': 199.99,
                'origin': 'MAD',
                'destination': 'CDG',
                'out_date': '2025-11-01',
                'return_date': '2025-11-10',
                'currency': 'EUR',
                'trip_type': 'round',
                'stop_overs': 1,
                'via_city': ['BCN'],
                'origin_city': 'Madrid',
                'destination_city': 'Paris'
            }
        """
        return {
            "price": self.price,
            "origin": self.origin_airport,
            "destination": self.destination_airport,
            "out_date": self.out_date,
            "return_date": self.return_date,
            "currency": self.currency,
            "trip_type": self.trip_type,
            "stop_overs": self.stop_overs,
            "via_city": self.via_city,
            "origin_city": self.origin_city,
            "destination_city": self.destination_city
        }

    def as_string(self) -> str:
        """
        Return a compact human-readable string of the flight details.

        Example:
            >>> flight.as_string()
            'MAD (Madrid) -> CDG (Paris) = 199.99 EUR [2025-11-01 TO 2025-11-10] (Round Trip) | Stops: 1 via BCN'
        """
        if self.price is None:
            return "❌ No valid flight data available."

        trip_label: str = "Round Trip" if self.trip_type == "round" else "One Way"

        via_str: str = ""
        if self.stop_overs > 0:
            via_str = f" | Stops: {self.stop_overs} via {', '.join(self.via_city)}"

        return (
            f"{self.origin_airport}{f' ({self.origin_city})' if self.origin_city else ''} -> "
            f"{self.destination_airport}{f' ({self.destination_city})' if self.destination_city else ''} = "
            f"{self.price} {self.currency} "
            f"[{self.out_date} TO {self.return_date}] "
            f"({trip_label}){via_str}"
        )


def find_cheapest_flight(flight_list: List[FlightData]) -> FlightData:
    """
    Find and return the cheapest flight from a list of FlightData objects.

    Args:
        flight_list (List[FlightData]): List of available flights.

    Returns:
        FlightData: The cheapest flight, or a dummy FlightData object if no flights are valid.

    Example:
        >>> flights = [
        ...     FlightData(320.50, "MAD", "PAR", "2025-10-15", "2025-10-20"),
        ...     FlightData(245.99, "MAD", "PAR", "2025-10-15", "2025-10-20"),
        ...     FlightData(299.99, "MAD", "PAR", "2025-10-15", "2025-10-20")
        ... ]
        >>> cheapest = find_cheapest_flight(flights)
        >>> cheapest.price
        245.99
    """
    if not flight_list:
        print("⚠️ No flight data found.")
        return FlightData("N/A", "N/A", "N/A", "N/A", "N/A")

    cheapest: FlightData = min(flight_list, key=lambda f: f.price if f.price else float("inf"))
    return cheapest


# ============================
# Optional Test Block
# ============================
if __name__ == "__main__":
    print("\n==============================")
    print("🧪 TEST: FlightData & Cheapest Flight")
    print("==============================")

    # Create mock flights
    flights: List[FlightData] = [
        FlightData(320.50, "MAD", "PAR", "2025-10-15", "2025-10-20", stop_overs=0, origin_city="Madrid", destination_city="Paris"),
        FlightData(245.99, "MAD", "PAR", "2025-10-15", "2025-10-20", stop_overs=1, via_city=["BCN"], origin_city="Madrid", destination_city="Paris"),  # cheapest
        FlightData(299.99, "MAD", "PAR", "2025-10-15", "2025-10-20", stop_overs=2, via_city=["LIS", "BRU"], origin_city="Madrid", destination_city="Paris"),
    ]

    for f in flights:
        print(f"🔹 {f.as_string()}")

    cheapest: FlightData = find_cheapest_flight(flights)
    print("\n🎯 Cheapest Flight:")
    print(cheapest.as_string())
