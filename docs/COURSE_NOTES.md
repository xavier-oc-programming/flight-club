# Course Notes — Day 40: Capstone Part 2 — Flight Club

## Exercise Description

**Course:** 100 Days of Code — The Complete Python Pro Bootcamp (Dr. Angela Yu)
**Day:** 40 — Capstone Project Part 2
**Topic:** APIs, OOP, Environment Variables, Notifications

### Goal

Build an automated flight deal finder called **Flight Club**. The program:

1. Connects to a **Google Sheet** (via Sheety API) to read a list of destination cities and
   their lowest acceptable prices.
2. Looks up the **IATA code** for each city using the Amadeus Location API and updates the
   sheet if any codes are missing.
3. Searches for **round-trip flight offers** from a fixed origin (Madrid, MAD) to each
   destination using the Amadeus Flight Offers API.
4. If no direct flights exist, retries the search with stopovers allowed.
5. Picks the **cheapest option** and notifies registered users via **SMS** (Twilio) and
   **email** (Gmail SMTP) if the price is below the user-defined threshold.

### APIs Used

| Service         | Purpose                                      |
|----------------|----------------------------------------------|
| Amadeus         | IATA code lookup + flight search             |
| Sheety          | Google Sheet as a REST API (destinations + users) |
| Twilio          | SMS notifications                            |
| Gmail SMTP      | Email notifications to all registered users  |

### Key Python Concepts Practiced

- Class-based architecture (DataManager, FlightSearch, FlightData, NotificationManager)
- Environment variables and `.env` files with `python-dotenv`
- OAuth2 token retrieval (Amadeus client credentials flow)
- HTTP requests with `requests` (GET, PUT, POST)
- SMTP email sending with `smtplib`
- `datetime` arithmetic for flight date windows
- Error handling and retry logic (direct → stopover fallback)
- Typing annotations (`Optional`, `List`, `Dict`, `tuple[...]`)
