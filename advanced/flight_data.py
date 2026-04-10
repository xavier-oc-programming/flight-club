import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class FlightData:
    """A structured container for a single flight offer."""

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
            "destination_city": self.destination_city,
        }

    def as_string(self) -> str:
        if self.price is None:
            return "No valid flight data available."

        trip_label = "Round Trip" if self.trip_type == "round" else "One Way"
        via_str = f" | Stops: {self.stop_overs} via {', '.join(self.via_city)}" if self.stop_overs > 0 else ""

        return (
            f"{self.origin_airport}{f' ({self.origin_city})' if self.origin_city else ''} -> "
            f"{self.destination_airport}{f' ({self.destination_city})' if self.destination_city else ''} = "
            f"{self.price} {self.currency} "
            f"[{self.out_date} TO {self.return_date}] "
            f"({trip_label}){via_str}"
        )


def find_cheapest_flight(flight_list: List[FlightData]) -> FlightData:
    """Return the cheapest flight from a list, or a null FlightData if the list is empty."""
    if not flight_list:
        return FlightData("N/A", "N/A", "N/A", "N/A", "N/A")
    return min(flight_list, key=lambda f: f.price if f.price else float("inf"))
