# Flight Club — Automated Flight Deal Scanner

Automated flight deal scanner that monitors destination prices via the Amadeus API and notifies users by SMS and email when a fare drops below a user-defined threshold.

For example, if you set London's threshold to €50, the bot searches all available round-trips from Madrid (MAD) to London across the next six months. When it finds a fare of €42, it sends you an SMS — "Flight Deal Alert! MAD → LHR = 42.0 EUR [2025-11-03 TO 2025-11-10] (Round Trip)" — and emails the same alert to every address registered in your Google Sheet.

Two builds are included. The **original** build is the course exercise as written: a single orchestration file that imports the helper modules verbatim, with only path fixes applied. The **advanced** build extracts every magic number and URL into `config.py`, refactors `NotificationManager` into a leaner `Notifier` that accepts plain strings (no hidden API calls inside), and wires everything through a clean `main()` function — making it easy to extend, test, or swap out any single component.

External services: **Amadeus** (OAuth2 flight search + IATA lookup), **Sheety** (Google Sheet as REST API for destinations and registered users), **Twilio** (SMS), and **Gmail SMTP** (email). Each requires its own credentials stored in `.env`.

---

## Table of Contents

0. [Prerequisites](#0-prerequisites)
1. [Quick Start](#1-quick-start)
2. [Builds Comparison](#2-builds-comparison)
3. [Usage](#3-usage)
4. [Data Flow](#4-data-flow)
5. [Features](#5-features)
6. [Navigation Flow](#6-navigation-flow)
7. [Architecture](#7-architecture)
8. [Module Reference](#8-module-reference)
9. [Configuration Reference](#9-configuration-reference)
10. [Data Schema](#10-data-schema)
11. [Environment Variables](#11-environment-variables)
12. [Design Decisions](#12-design-decisions)
13. [Course Context](#13-course-context)
14. [Dependencies](#14-dependencies)

---

## 0. Prerequisites

| Service | What you need | Where to get it |
|---------|--------------|-----------------|
| Amadeus | API Key + Secret (free test account) | [developer.amadeus.com](https://developer.amadeus.com) → My Apps |
| Sheety | Endpoint URL + Basic Auth credentials | [sheety.co](https://sheety.co) → create project from your Google Sheet |
| Twilio | Account SID + Auth Token + phone number | [twilio.com](https://twilio.com) → Console Dashboard |
| Gmail | App Password (16 chars, requires 2FA) | myaccount.google.com → Security → App Passwords |

**Google Sheet structure required:**

*prices* sheet — columns: `city`, `iataCode`, `lowestPrice`
*users* sheet — columns: `whatIsYourFirstName?`, `whatIsYourLastName?`, `whatIsYourEmail?`

---

## 1. Quick Start

```bash
git clone https://github.com/xavier-oc-programming/flight-club.git
cd flight-club
pip install -r requirements.txt

cp .env.example .env
# fill in .env with your real credentials

python menu.py        # interactive menu
# or run directly:
python advanced/main.py
```

---

## 2. Builds Comparison

| Feature | Original | Advanced |
|---------|----------|----------|
| Entry point | `original/main.py` | `advanced/main.py` |
| Constants | Inline | `config.py` |
| `Notifier` | Fetches emails internally | Accepts recipients list (injected) |
| `load_dotenv` path | Relative (cwd-dependent) | Absolute (`Path(__file__).parent.parent`) |
| Print statements | Emoji-heavy | Clean output |
| Module imports | Flat (same directory) | `sys.path.insert` + explicit `.env` path |

---

## 3. Usage

```
python menu.py
```

```
 ███████╗██╗     ██╗ ██████╗ ██╗  ██╗████████╗ ...
 ...
======================================================================
  Select a build to run:

  1  Original   — course exercise, single file
  2  Advanced   — refactored build with config, classes & modules

  q  Quit
======================================================================

Your choice: 2

Token retrieved. Expires in 1799 seconds.
Searching round-trip flights from MAD...

Checking flights to Paris (PAR)...
Found flight options:
  MAD -> CDG = 49.99 EUR [2025-11-03 TO 2025-11-10] (Round Trip)
  MAD -> ORY = 54.20 EUR [2025-11-07 TO 2025-11-14] (Round Trip)

Cheapest: MAD -> CDG = 49.99 EUR [2025-11-03 TO 2025-11-10] (Round Trip)
Threshold: 54 EUR
Price below threshold — sending notifications...
SMS sent. SID: SM...
Email sent to alice@example.com

Press Enter to return to menu...
```

---

## 4. Data Flow

```
Input (Google Sheet via Sheety)
  └─► DataManager.get_destination_data()
        └─► list of {city, iataCode, lowestPrice}

IATA Lookup (Amadeus Location API)
  └─► FlightSearch.get_destination_code() / get_destination_codes()
        └─► fills any blank iataCode fields
        └─► DataManager.update_destination_codes() → writes back to Sheet

Flight Search (Amadeus Flight Offers API)
  └─► FlightSearch.check_flights(is_direct=True)
        └─► if empty → retry with is_direct=False
        └─► returns list[FlightData]

Processing
  └─► find_cheapest_flight(flights) → FlightData

Output (if price < threshold)
  └─► Notifier.send_sms(message)
  └─► DataManager.get_customer_emails()
        └─► Notifier.send_emails(message, recipients)
```

---

## 5. Features

### Both builds
- Fetches destination list and price thresholds from Google Sheet
- Auto-fills missing IATA codes via Amadeus and updates the sheet
- Searches direct flights first; retries with stopovers if none found
- Expands cities with no city code to individual airport codes
- Sends SMS via Twilio when cheapest price is below threshold
- Sends email to all registered users when price is below threshold

### Advanced-only
- All URLs, limits, delays, and defaults isolated in `config.py`
- `Notifier` is pure I/O — accepts message string + recipient list, no hidden fetches
- Absolute `load_dotenv` path works regardless of working directory
- Clean separation: fetch → process → notify with no cross-module side effects

---

## 6. Navigation Flow

```
menu.py
├── 1 → original/main.py
│         Initializes: DataManager, FlightSearch, NotificationManager
│         Flow: fetch sheet → fill IATA → update sheet → search flights
│               → pick cheapest → send SMS + emails if below threshold
│
└── 2 → advanced/main.py
          Initializes: DataManager, FlightSearch, Notifier
          Flow: same logic, constants from config.py
                Notifier receives plain strings — no internal API calls
```

---

## 7. Architecture

```
flight-club/
├── menu.py                   # Interactive launcher
├── art.py                    # LOGO constant
├── requirements.txt          # pip dependencies
├── .env.example              # credential template
├── .gitignore
├── docs/
│   └── COURSE_NOTES.md       # Original exercise description
│
├── original/                 # Course exercise (verbatim + path fixes)
│   ├── main.py               # Orchestrator
│   ├── data_manager.py       # Sheety API client
│   ├── flight_search.py      # Amadeus API client
│   ├── flight_data.py        # FlightData model + find_cheapest_flight
│   ├── notification_manager.py  # Twilio + SMTP sender
│   └── test_email.py         # SMTP connectivity test script
│
└── advanced/                 # Refactored build
    ├── config.py             # All constants
    ├── main.py               # Orchestrator
    ├── data_manager.py       # Sheety API client
    ├── flight_search.py      # Amadeus API client
    ├── flight_data.py        # FlightData model + find_cheapest_flight
    └── notifier.py           # Pure I/O notifier (SMS + email)
```

---

## 8. Module Reference

### `advanced/flight_search.py` — `FlightSearch`

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | — | Loads API credentials, fetches OAuth2 token |
| `_get_new_token()` | `str` | Requests a new Amadeus bearer token |
| `get_destination_code(city_name)` | `str` | Returns IATA city code or `"N/A"` |
| `get_destination_codes(city_name)` | `list[str]` | Returns all airport codes for a city |
| `check_flights(origin, dest, from_time, to_time, is_direct)` | `tuple[list[FlightData] \| None, list[dict] \| None]` | Queries flight offers; returns flights or error list |

### `advanced/data_manager.py` — `DataManager`

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | — | Loads Sheety credentials and endpoints |
| `get_destination_data()` | `list[dict]` | Fetches and caches all rows from 'prices' sheet |
| `update_destination_codes()` | `None` | Writes iataCode back for each cached row |
| `get_customer_emails()` | `list[dict]` | Fetches firstName, lastName, email from 'users' sheet |

### `advanced/flight_data.py`

| Symbol | Returns | Description |
|--------|---------|-------------|
| `FlightData.__init__(...)` | — | Stores price, airports, dates, stops, cities |
| `FlightData.to_dict()` | `dict` | All fields as a dictionary |
| `FlightData.as_string()` | `str` | Human-readable one-liner (e.g. `MAD → CDG = 49.99 EUR`) |
| `find_cheapest_flight(flight_list)` | `FlightData` | Returns cheapest by price; null object if list empty |

### `advanced/notifier.py` — `Notifier`

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(email_subject, smtp_server, smtp_port)` | — | Initialises Twilio client and email config |
| `send_sms(message_body)` | `None` | Sends SMS via Twilio; raises on failure |
| `send_emails(message_body, recipients)` | `None` | Sends email to each address via SMTP; raises on failure |

---

## 9. Configuration Reference

All in `advanced/config.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `TOKEN_ENDPOINT` | Amadeus OAuth2 URL | Endpoint to fetch bearer token |
| `IATA_ENDPOINT` | Amadeus Locations URL | IATA city/airport code lookup |
| `FLIGHT_ENDPOINT` | Amadeus Flight Offers URL | Flight search endpoint |
| `ORIGIN_CITY_IATA` | `"MAD"` | Fixed departure city (Madrid) |
| `SEARCH_WINDOW_DAYS` | `180` | Days ahead for return date |
| `MAX_FLIGHT_RESULTS` | `5` | Max offers per Amadeus query |
| `IATA_LOOKUP_DELAY` | `1.5` | Seconds between IATA lookups (rate limit) |
| `DEFAULT_CURRENCY` | `"EUR"` | Currency for price display |
| `EMAIL_SUBJECT` | `"✈️ Flight Deal Alert!"` | Email subject line |
| `SMTP_SERVER_DEFAULT` | `"smtp.gmail.com"` | SMTP server |
| `SMTP_PORT_DEFAULT` | `587` | SMTP port (STARTTLS) |

---

## 10. Data Schema

### Sheety 'prices' sheet row

```json
{
  "id": 2,
  "city": "Paris",
  "iataCode": "PAR",
  "lowestPrice": 54
}
```

### Sheety 'users' sheet row (raw)

```json
{
  "whatIsYourFirstName?": "Alice",
  "whatIsYourLastName?": "Smith",
  "whatIsYourEmail?": "alice@example.com"
}
```

### `FlightData.to_dict()` output

```json
{
  "price": 49.99,
  "origin": "MAD",
  "destination": "CDG",
  "out_date": "2025-11-03",
  "return_date": "2025-11-10",
  "currency": "EUR",
  "trip_type": "round",
  "stop_overs": 0,
  "via_city": [],
  "origin_city": null,
  "destination_city": null
}
```

---

## 11. Environment Variables

Copy `.env.example` → `.env` and fill in your credentials.

| Variable | Required | Description |
|----------|----------|-------------|
| `SHEETY_PRICES_ENDPOINT` | Yes | Sheety URL for the 'prices' sheet |
| `SHEETY_USERS_ENDPOINT` | Yes | Sheety URL for the 'users' sheet |
| `SHEETY_USERNAME` | Yes | Sheety Basic Auth username |
| `SHEETY_PASSWORD` | Yes | Sheety Basic Auth password |
| `API_KEY_AMADEUS` | Yes | Amadeus API key |
| `SECRET_AMADEUS` | Yes | Amadeus API secret |
| `TWILIO_ACCOUNT_SID` | Yes | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio Auth Token |
| `TWILIO_FROM` | Yes | Twilio sender number (E.164) |
| `TWILIO_TO` | Yes | Your mobile number (E.164) |
| `TWILIO_WHATSAPP_FROM` | Optional | WhatsApp sender (`whatsapp:+14155238886`) |
| `TWILIO_WHATSAPP_TO` | Optional | Your WhatsApp number |
| `CURRENCY` | Optional | Price currency code (default: `EUR`) |
| `EMAIL_ADDRESS` | Yes | Gmail sender address |
| `EMAIL_PASSWORD` | Yes | Gmail 16-char App Password |
| `SMTP_SERVER` | Optional | SMTP host (default: `smtp.gmail.com`) |
| `SMTP_PORT` | Optional | SMTP port (default: `587`) |

---

## 12. Design Decisions

**Amadeus test environment** — The free developer tier uses `test.api.amadeus.com`. Results are simulated but structurally identical to production. Switching to production requires changing three URL constants in `config.py`.

**City code → airport code fallback** — Some cities have no IATA city code (e.g. smaller destinations). The search first tries the city code; if Amadeus returns `N/A`, it queries for individual airport codes and searches each one. This maximises coverage without requiring manual data entry.

**Direct → stopover retry** — Direct-only searches fail silently for routes with no nonstop service. Retrying with `nonStop=false` recovers these routes at the cost of one extra API call per destination.

**`IATA_LOOKUP_DELAY`** — Amadeus free tier enforces a rate limit. A 1.5s sleep between IATA lookups prevents HTTP 429 errors when the sheet has many destinations.

**Notifier takes plain strings, not FlightData** — In the original build, `NotificationManager` formats the message internally using `FlightData`. This ties the notifier to the data model. In the advanced build, `main()` formats the string and passes it in — `Notifier` becomes a pure I/O class that can send any message, making it easy to change the format or reuse it elsewhere.

**Notifier raises on failure** — Instead of swallowing exceptions with `print(f"Failed: {e}")`, the advanced `Notifier` raises. `main()` catches each call independently so an SMS failure does not prevent email delivery (and vice versa).

**Absolute `load_dotenv` path** — `load_dotenv()` with no argument resolves `.env` relative to the current working directory. If `main.py` is launched from a different directory (e.g. via `menu.py`), the `.env` is not found. Using `Path(__file__).parent.parent / ".env"` makes the path absolute and launch-directory-independent.

**`sys.path.insert` in advanced modules** — Python's import system resolves modules relative to `sys.path`. Since `advanced/` is a subdirectory (not a package), sibling imports (`from config import ...`) require inserting the module's own directory at the front of `sys.path`.

---

## 13. Course Context

**Course:** 100 Days of Code — The Complete Python Pro Bootcamp (Dr. Angela Yu)
**Day:** 40 — Capstone Part 2: Flight Club

The project introduces multi-API orchestration: authenticating with OAuth2, reading and writing a Google Sheet via a REST wrapper (Sheety), chaining API responses across services, and delivering notifications through two independent channels. It builds on the OOP patterns from Days 16–20 and the API work from Days 33–36.

---

## 14. Dependencies

| Module | Used in | Purpose |
|--------|---------|---------|
| `requests` | `flight_search.py`, `data_manager.py` | HTTP calls to Amadeus and Sheety |
| `python-dotenv` | all modules | Load credentials from `.env` |
| `twilio` | `notifier.py` / `notification_manager.py` | Send SMS alerts |
| `smtplib` | `notifier.py` / `notification_manager.py` | Send email via Gmail SMTP |
| `datetime` | `main.py` | Calculate departure and return date windows |
| `pathlib` | all modules | Resolve `.env` and script paths portably |
