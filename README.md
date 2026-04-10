# Flight Club — Automated Flight Deal Scanner

Automated flight deal scanner that searches Google Flights via SerpApi and notifies users by WhatsApp and email when a fare drops below a user-defined threshold.

For example, if you set Frankfurt's threshold to €400, the bot searches round-trips from Madrid (MAD) to Frankfurt for the next six months. When it finds a fare of €378, it sends a WhatsApp message — "✈️ Flight Deal Alert! MAD → FRA (Frankfurt) | Price: 378.0 EUR | Depart: 2026-04-11 | Return: 2026-10-07" — and emails the same alert to every address registered in your Google Sheet.

Two builds are included. The **original** build is the course exercise as written: a single orchestration file that imports the helper modules verbatim, with only path fixes applied. The **advanced** build extracts every magic number and URL into `config.py`, refactors `NotificationManager` into a leaner `Notifier` that accepts plain strings (no hidden API calls inside), and wires everything through a clean `main()` function — making it easy to extend, test, or swap out any single component.

External services: **SerpApi** (Google Flights search), **Sheety** (Google Sheet as REST API for destinations and registered users), **Twilio** (WhatsApp), and **Gmail SMTP** (email). Each requires its own credentials stored in `.env`.

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
| SerpApi | API key (free tier: 100 searches/month) | [serpapi.com](https://serpapi.com) → Dashboard → API Key |
| Sheety | Endpoint URL + Basic Auth credentials | [sheety.co](https://sheety.co) → create project from your Google Sheet |
| Twilio | Account SID + Auth Token + WhatsApp sandbox | [twilio.com](https://twilio.com) → Messaging → Try it out → Send a WhatsApp message |
| Gmail | App Password (16 chars, requires 2FA) | myaccount.google.com → Security → App Passwords |

**Google Sheet structure required:**

*prices* sheet — columns: `city`, `iataCode`, `lowestPrice`
*users* sheet — columns: `whatIsYourFirstName?`, `whatIsYourLastName?`, `whatIsYourEmail?`

> **Note:** SerpApi has no IATA lookup endpoint. Airport codes must be entered directly in the `iataCode` column of the sheet before running.

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
| Flight API | SerpApi (Google Flights) | SerpApi (Google Flights) |
| Notification | WhatsApp + Email | WhatsApp + Email |
| Constants | Inline | `config.py` |
| `Notifier` | Fetches emails internally | Accepts recipients list (injected) |
| `load_dotenv` path | Relative (cwd-dependent) | Absolute (`Path(__file__).parent.parent`) |
| Print style | Emoji-heavy | Clean structured output |
| Module imports | Flat (same directory) | `sys.path.insert` + explicit `.env` path |

---

## 3. Usage

```
python menu.py
```

```
 ███████╗██╗     ██╗ ██████╗ ...
======================================================================
  Select a build to run:

  1  Original   — course exercise, single file
  2  Advanced   — refactored build with config, classes & modules

  q  Quit
======================================================================

Your choice: 2

Scanning flights from MAD

──────────────────────────────────────────────────
Frankfurt (FRA)
  MAD -> FRA = 378.0 EUR [2026-04-11 TO 2026-10-07] (Round Trip)
  MAD -> FRA = 653.0 EUR [2026-04-11 TO 2026-10-07] (Round Trip) | Stops: 1 via AMS

  Cheapest : 378.0 EUR
  Threshold: 400 EUR
  Deal found! 378.0 EUR is under your 400 EUR target.
  WhatsApp ✓
  Email ✓  (1 recipient(s))

──────────────────────────────────────────────────
Istanbul (IST)
  MAD -> IST = 322.0 EUR [2026-04-11 TO 2026-10-07] (Round Trip)

  Cheapest : 322.0 EUR
  Threshold: 300 EUR
  No deal — 322.0 EUR is above the 300 EUR target.

──────────────────────────────────────────────────
Done.

Press Enter to return to menu...
```

---

## 4. Data Flow

```
Input (Google Sheet via Sheety)
  └─► DataManager.get_destination_data()
        └─► list of {city, iataCode, lowestPrice}

IATA Codes
  └─► Must be pre-filled in the sheet manually
        └─► DataManager.update_destination_codes() writes back any newly fetched codes

Flight Search (Google Flights via SerpApi)
  └─► FlightSearch.check_flights(is_direct=True)
        └─► if empty → retry with is_direct=False (max_stopovers=2)
        └─► returns list[FlightData]

Processing
  └─► find_cheapest_flight(flights) → FlightData

Output (if price < threshold)
  └─► Notifier.send_whatsapp(message)
  └─► DataManager.get_customer_emails()
        └─► Notifier.send_emails(message, recipients)
```

---

## 5. Features

### Both builds
- Fetches destination list and price thresholds from Google Sheet
- Searches direct flights first; retries with stopovers if none found
- Picks the cheapest offer and compares against the sheet threshold
- Sends WhatsApp via Twilio when cheapest price is below threshold
- Sends email to all registered users when price is below threshold

### Advanced-only
- All URLs, limits, delays, and defaults isolated in `config.py`
- `Notifier` is pure I/O — accepts message string + recipient list, no hidden fetches
- WhatsApp message formatted with structured fields (price, dates, stops)
- Absolute `load_dotenv` path works regardless of working directory
- Clean separator output between each destination
- WhatsApp and email failures caught independently

---

## 6. Navigation Flow

```
menu.py
├── 1 → original/main.py
│         Initializes: DataManager, FlightSearch, NotificationManager
│         Flow: fetch sheet → search flights → pick cheapest
│               → send WhatsApp + emails if below threshold
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
│   ├── flight_search.py      # SerpApi client
│   ├── flight_data.py        # FlightData model + find_cheapest_flight
│   ├── notification_manager.py  # Twilio WhatsApp + SMTP sender
│   └── test_email.py         # SMTP connectivity test script
│
└── advanced/                 # Refactored build
    ├── config.py             # All constants
    ├── main.py               # Orchestrator
    ├── data_manager.py       # Sheety API client
    ├── flight_search.py      # SerpApi client
    ├── flight_data.py        # FlightData model + find_cheapest_flight
    └── notifier.py           # Pure I/O notifier (WhatsApp + email)
```

---

## 8. Module Reference

### `advanced/flight_search.py` — `FlightSearch`

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__()` | — | Loads SerpApi key from environment |
| `get_destination_code(city_name)` | `str` | Not supported — returns `"N/A"` (add codes to sheet manually) |
| `get_destination_codes(city_name)` | `list[str]` | Not supported — returns `[]` |
| `check_flights(origin, dest, from_time, to_time, is_direct)` | `tuple[list[FlightData] \| None, list[dict] \| None]` | Queries Google Flights; returns flights or error list |

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
| `FlightData.as_string()` | `str` | Human-readable one-liner (e.g. `MAD -> FRA = 378.0 EUR`) |
| `find_cheapest_flight(flight_list)` | `FlightData` | Returns cheapest by price; null object if list empty |

### `advanced/notifier.py` — `Notifier`

| Method | Returns | Description |
|--------|---------|-------------|
| `__init__(email_subject, smtp_server, smtp_port)` | — | Initialises Twilio client and email config |
| `send_whatsapp(message_body)` | `None` | Sends WhatsApp via Twilio sandbox; raises on failure |
| `send_emails(message_body, recipients)` | `None` | Sends email to each address via SMTP; raises on failure |

---

## 9. Configuration Reference

All in `advanced/config.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `SERPAPI_ENDPOINT` | SerpApi search URL | Google Flights search endpoint |
| `ORIGIN_CITY_IATA` | `"MAD"` | Fixed departure city (Madrid) |
| `SEARCH_WINDOW_DAYS` | `180` | Days ahead for return date |
| `MAX_FLIGHT_RESULTS` | `5` | Max offers parsed per search |
| `IATA_LOOKUP_DELAY` | `1.5` | Seconds between IATA lookups if used |
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
  "city": "Frankfurt",
  "iataCode": "FRA",
  "lowestPrice": 400
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
  "price": 378.0,
  "origin": "MAD",
  "destination": "FRA",
  "out_date": "2026-04-11",
  "return_date": "2026-10-07",
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
| `SERPAPI_KEY` | Yes | SerpApi API key |
| `TWILIO_ACCOUNT_SID` | Yes | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Yes | Twilio Auth Token |
| `TWILIO_WHATSAPP_FROM` | Yes | Twilio sandbox sender (`whatsapp:+14155238886`) |
| `TWILIO_WHATSAPP_TO` | Yes | Your WhatsApp number (e.g. `whatsapp:+34611122334`) |
| `CURRENCY` | Optional | Price currency code (default: `EUR`) |
| `EMAIL_ADDRESS` | Yes | Gmail sender address |
| `EMAIL_PASSWORD` | Yes | Gmail 16-char App Password |
| `SMTP_SERVER` | Optional | SMTP host (default: `smtp.gmail.com`) |
| `SMTP_PORT` | Optional | SMTP port (default: `587`) |

---

## 12. Design Decisions

**SerpApi over Amadeus** — The original course used the Amadeus test API, which was decommissioned in 2026. SerpApi scrapes Google Flights and returns real-time prices with a simple API key — no OAuth2 flow, no test/production environment split. The trade-off is 100 searches/month on the free tier (vs unlimited on Amadeus test), which covers ~5 full runs with 9 destinations.

**No IATA auto-lookup** — Amadeus provided a locations endpoint for resolving city names to IATA codes. SerpApi does not. Airport codes must be entered once in the Google Sheet. This is a one-time manual step, not a recurring cost.

**WhatsApp over SMS** — The Twilio WhatsApp sandbox is free and requires no phone number purchase. Standard SMS requires a paid Twilio number. For a personal project, WhatsApp delivers the same result at zero cost. The sandbox requires re-joining every ~72 hours of inactivity.

**Direct → stopover retry** — Direct-only searches return no results for many long-haul routes. Retrying with `max_stopovers=2` recovers these at the cost of one extra API call per destination.

**Structured WhatsApp message** — The message sent to WhatsApp is formatted with labelled fields (Price, Depart, Return, Stops) rather than the compact `as_string()` format, which is harder to read on a mobile notification.

**Notifier takes plain strings, not FlightData** — In the original build, `NotificationManager` formats the message internally. This ties the notifier to the data model. In the advanced build, `main()` formats the string and passes it in — `Notifier` becomes a pure I/O class that can send any message.

**Notifier raises on failure** — `main()` catches WhatsApp and email calls independently, so a WhatsApp failure does not prevent email delivery and vice versa.

**Absolute `load_dotenv` path** — `load_dotenv()` with no argument resolves `.env` relative to the current working directory. Using `Path(__file__).parent.parent / ".env"` makes it launch-directory-independent.

---

## 13. Course Context

**Course:** 100 Days of Code — The Complete Python Pro Bootcamp (Dr. Angela Yu)
**Day:** 40 — Capstone Part 2: Flight Club

The project introduces multi-API orchestration: reading and writing a Google Sheet via a REST wrapper (Sheety), chaining API responses across services, and delivering notifications through two independent channels. It builds on the OOP patterns from Days 16–20 and the API work from Days 33–36.

---

## 14. Dependencies

| Module | Used in | Purpose |
|--------|---------|---------|
| `requests` | `flight_search.py`, `data_manager.py` | HTTP calls to SerpApi and Sheety |
| `python-dotenv` | all modules | Load credentials from `.env` |
| `twilio` | `notifier.py` / `notification_manager.py` | Send WhatsApp alerts |
| `smtplib` | `notifier.py` / `notification_manager.py` | Send email via Gmail SMTP |
| `datetime` | `main.py` | Calculate departure and return date windows |
| `pathlib` | all modules | Resolve `.env` and script paths portably |
