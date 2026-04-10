# URLs — Amadeus API
TOKEN_ENDPOINT = "https://test.api.amadeus.com/v1/security/oauth2/token"
IATA_ENDPOINT = "https://test.api.amadeus.com/v1/reference-data/locations"
FLIGHT_ENDPOINT = "https://test.api.amadeus.com/v2/shopping/flight-offers"

# Search parameters
ORIGIN_CITY_IATA = "MAD"
SEARCH_WINDOW_DAYS = 180   # how many days ahead to search for return flights
MAX_FLIGHT_RESULTS = 5     # max offers per Amadeus query

# Timing / rate limits
IATA_LOOKUP_DELAY = 1.5    # seconds between IATA lookups to stay within free-tier rate limit

# Output / formatting
DEFAULT_CURRENCY = "EUR"
EMAIL_SUBJECT = "✈️ Flight Deal Alert!"
SMTP_SERVER_DEFAULT = "smtp.gmail.com"
SMTP_PORT_DEFAULT = 587
