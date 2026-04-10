import os
import requests
from pathlib import Path
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class DataManager:
    """Sheety API client — reads/writes destination and user data from Google Sheets."""

    def __init__(self) -> None:
        self._authorization = HTTPBasicAuth(
            os.environ["SHEETY_USERNAME"],
            os.environ["SHEETY_PASSWORD"],
        )
        self._prices_endpoint: str = os.environ["SHEETY_PRICES_ENDPOINT"]
        self._users_endpoint: str = os.environ["SHEETY_USERS_ENDPOINT"]
        self.destination_data: List[Dict[str, Any]] = []

    def get_destination_data(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the 'prices' sheet and cache them."""
        response = requests.get(url=self._prices_endpoint, auth=self._authorization)
        response.raise_for_status()
        self.destination_data = response.json()["prices"]
        return self.destination_data

    def update_destination_codes(self) -> None:
        """Write back the iataCode field for each row in the 'prices' sheet."""
        for city in self.destination_data:
            new_data = {"price": {"iataCode": city["iataCode"]}}
            response = requests.put(
                url=f"{self._prices_endpoint}/{city['id']}",
                json=new_data,
                auth=self._authorization,
            )
            response.raise_for_status()
            code = city["iataCode"]
            if code == "N/A":
                print(f"Skipped {city['city']} (invalid IATA code)")
            else:
                print(f"Updated {city['city']}: {code}")

    def get_customer_emails(self) -> List[Dict[str, str]]:
        """
        Fetch customer records from the 'users' sheet.

        Returns a list of dicts with keys: firstName, lastName, email.
        """
        response = requests.get(url=self._users_endpoint, auth=self._authorization)
        response.raise_for_status()
        users = response.json()["users"]
        return [
            {
                "firstName": user.get("whatIsYourFirstName?", ""),
                "lastName": user.get("whatIsYourLastName?", ""),
                "email": user.get("whatIsYourEmail?", ""),
            }
            for user in users
        ]
