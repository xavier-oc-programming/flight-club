"""
data_manager.py

This module handles data interaction with a Google Sheet via the Sheety API.

Key responsibilities:
- Fetch destination data (including city names and IATA codes).
- Update IATA codes in the Google Sheet using HTTP Basic Auth.
- Fetch customer emails from a separate 'users' sheet.

Environment Variables required in `.env`:
- SHEETY_PRICES_ENDPOINT: The full Sheety API URL for the 'prices' sheet.
- SHEETY_USERS_ENDPOINT: The full Sheety API URL for the 'users' sheet.
- SHEETY_USERNAME: Username used for HTTP Basic Auth.
- SHEETY_PASSWORD: Password used for HTTP Basic Auth.

Usage:
    from data_manager import DataManager

    dm = DataManager()
    destinations = dm.get_destination_data()
    dm.update_destination_codes()
    emails = dm.get_customer_emails()
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from pprint import pprint
from typing import List, Dict, Any

# Load environment variables from the .env file
load_dotenv()


class DataManager:

    """
        A class to interact with the Sheety API and manage flight deal data
        stored in Google Sheets.

        Attributes:
            _user (str): Sheety Basic Auth username from `.env`.
                Example: "trial_user_01"

            _password (str): Sheety Basic Auth password from `.env`.
                Example: "securePassword123"

            _authorization (HTTPBasicAuth): Auth object for authenticated requests.
                Example: HTTPBasicAuth("trial_user_01", "securePassword123")

            _prices_endpoint (str): URL of the Sheety 'prices' sheet.
                Example: "https://api.sheety.co/abc123/flightDeals/prices"

            _users_endpoint (str): URL of the Sheety 'users' sheet.
                Example: "https://api.sheety.co/abc123/flightDeals/users"

            destination_data (List[Dict[str, Any]]): Cached list of destinations pulled from the sheet.
                Example:
                    [
                        {"city": "Paris", "iataCode": "PAR", "lowestPrice": 54, "id": 2},
                        {"city": "Tokyo", "iataCode": "TYO", "lowestPrice": 600, "id": 3}
                    ]

        Methods:
            __init__():
                Initialize with credentials and endpoints from environment variables.

            get_destination_data() -> List[Dict[str, Any]]:
                Fetch all rows from the 'prices' sheet and store them in memory.

            update_destination_codes() -> None:
                Update the 'iataCode' field for each city in the 'prices' sheet.

            get_customer_emails() -> List[Dict[str, str]]:
                Fetch and clean customer data from the 'users' sheet, returning only
                firstName, lastName, and email fields.
    """




    def __init__(self) -> None:
        """Initialize with credentials and endpoints from environment variables."""
        self._user: str = os.environ["SHEETY_USERNAME"]
        self._password: str = os.environ["SHEETY_PASSWORD"]
        self._authorization: HTTPBasicAuth = HTTPBasicAuth(self._user, self._password)

        self._prices_endpoint: str = os.getenv("SHEETY_PRICES_ENDPOINT", "")
        self._users_endpoint: str = os.getenv("SHEETY_USERS_ENDPOINT", "")

        self.destination_data: List[Dict[str, Any]] = []

    def get_destination_data(self) -> List[Dict[str, Any]]:
        """
        Fetch all flight deal rows from the 'prices' sheet.

        Returns:
            list[dict]: Each row contains:
                - id (int): Row ID in the sheet
                - city (str): City name
                - iataCode (str): IATA code for the city
                - lowestPrice (int): User-defined lowest price threshold

        Example:
            >>> dm = DataManager()
            >>> data = dm.get_destination_data()
            >>> data[0]
            {'city': 'Paris', 'iataCode': 'PAR', 'lowestPrice': 200, 'id': 2}
        """
        response = requests.get(url=self._prices_endpoint, auth=self._authorization)
        response.raise_for_status()
        data = response.json()
        self.destination_data = data["prices"]
        return self.destination_data

    def update_destination_codes(self) -> None:
        """
        Update the 'iataCode' field in the Google Sheet for each city.

        Iterates through self.destination_data and updates Sheety row by row.

        Example:
            >>> dm = DataManager()
            >>> dm.destination_data = [{'city': 'Paris', 'iataCode': 'PAR', 'id': 2}]
            >>> dm.update_destination_codes()
            ✅ Updated Paris: PAR
        """
        for city in self.destination_data:
            new_data = {"price": {"iataCode": city["iataCode"]}}
            response = requests.put(
                url=f"{self._prices_endpoint}/{city['id']}",
                json=new_data,
                auth=self._authorization
            )
            response.raise_for_status()

            code: str = city["iataCode"]
            if code == "N/A":
                print(f"⚠️ Skipped {city['city']} (invalid IATA code)")
            else:
                print(f"✅ Updated {city['city']}: {code}")



    def get_customer_emails(self) -> List[Dict[str, str]]:
        """
        Fetch and clean customer data (emails + names) from the 'users' sheet.

        This method queries the Sheety API `users` endpoint, retrieves all rows,
        and normalizes the keys to return only the fields we care about:
        `firstName`, `lastName`, and `email`.  
        It also removes extraneous fields such as `id` and `timestamp`.

        Returns:
            List[Dict[str, str]]: A list of dictionaries where each dictionary
            represents a single customer.

            Each dictionary contains:
                - "firstName" (str): Customer's first name
                - "lastName"  (str): Customer's last name
                - "email"     (str): Customer's email address

        Example:
            >>> dm = DataManager()
            >>> customers = dm.get_customer_emails()
            >>> customers
            [
                {"firstName": "Dummy_first", "lastName": "Dummy_last", "email": "dummy@gmail.com"},
                {"firstName": "Alice", "lastName": "Smith", "email": "alice@example.com"}
            ]

        Notes:
            • If a key does not exist (e.g., missing first name), the value will be an empty string.
            • This method assumes your Google Sheet headers are named:
            "whatIsYourFirstName?", "whatIsYourLastName?", "whatIsYourEmail?"
        """
        response = requests.get(url=self._users_endpoint, auth=self._authorization)
        response.raise_for_status()
        data: Dict[str, List[Dict[str, str]]] = response.json()
        users: List[Dict[str, str]] = data["users"]

        cleaned_users: List[Dict[str, str]] = [
            {
                "firstName": user.get("whatIsYourFirstName?", ""),
                "lastName": user.get("whatIsYourLastName?", ""),
                "email": user.get("whatIsYourEmail?", "")
            }
            for user in users
        ]
        return cleaned_users



# ============================
# Optional: Test Block
# ============================
if __name__ == "__main__":
    dm = DataManager()

    # --- Test fetching destination data ---
    print("\n📥 Fetching destination data...")
    sheet_data = dm.get_destination_data()
    pprint(sheet_data)

    # --- Test updating IATA codes ---
    print("\n✏️ Updating destination codes...")
    dm.update_destination_codes()

    # --- Test fetching customer emails ---
    print("\n📧 Fetching customer emails...")
    users = dm.get_customer_emails()
    pprint(users)
