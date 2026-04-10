# URLs — SerpApi Google Flights
SERPAPI_ENDPOINT = "https://serpapi.com/search"

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
