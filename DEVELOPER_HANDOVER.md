# Developer handover: Playtomic booking bot – payment API impasse

**Purpose:** So another developer can take over without re-trying approaches that already failed. This document records what was done, what didn’t work, and what has **not** been tried yet.

**Last updated:** 2026-01-29

---

## Current problem

- The bot **logs in** and **fetches availability** successfully (playtomic.com, session/cookie auth).
- **Creating a booking** fails because the payment API returns **HTML** (the web app’s login/app page) instead of JSON, leading to: *"Payment API returned HTML instead of JSON"*.
- The bot is configured to **only book when a 0 EUR option exists** (subscription, included, pay at club). If the payment intent would require payment (e.g. €20), the bot does not book and logs a clear message.

---

## What was done (and outcome)

### 1. playtomic.io login and payment path

- **Change:** Bot tries to log in at `https://playtomic.io/api/v3/auth/login` to get a Bearer token. If that succeeds, payment calls (`create_payment_intent`, `update_payment_intent`, `confirm_reservation`) are sent to `https://playtomic.io/api/v1/payment_intents` with that token.
- **Result:** playtomic.io login **consistently fails** (non-JSON response, e.g. `Expecting value: line 1 column 1 (char 0)`). No token is obtained; this payment path is never used.

### 2. Fallback: api.playtomic.io with web login token

- **Change:** If playtomic.io login fails, the bot tries to use a Bearer token from the **playtomic.com** web login with `https://api.playtomic.io/v1/payment_intents`.
- **Result:** playtomic.com web login is **session/cookie-based**; it does **not** return a reusable Bearer token. So this fallback path is never used.

### 3. Final fallback: app.playtomic.com (session)

- **Change:** When neither playtomic.io nor api.playtomic.io can be used, the bot calls `https://app.playtomic.com/api/v1/payment_intents` (and warms up with a GET to `app.playtomic.com/payments?type=CUSTOMER_MATCH&...`).
- **Result:** That URL returns **HTML** (the app’s page), not JSON. So programmatic booking from the script fails with "Payment API returned HTML instead of JSON".

### 4. Only book when 0 EUR; clear message when payment required

- **Change:** Bot only attempts to book when a 0 EUR option is available. If the payment intent would require payment, it does not book and logs a clear message directing the user to the app or manual booking.
- **Result:** Working as intended; avoids blind attempts when payment is required.

### 5. Improved error logging and PAYMENT_API_TROUBLESHOOTING.md

- **Change:** Error messages now clearly state when the Payment API returns HTML and point the user to `PAYMENT_API_TROUBLESHOOTING.md` for manual browser capture.
- **Result:** Users get clear logs; troubleshooting doc exists.

### 6. User attempt to capture the “Continue - €0.00” request in DevTools

- **What was tried:** Chrome DevTools → Network tab → filter **Fetch/XHR**, then **All**. Clear list, click **"Continue - €0.00"** on the slot modal on playtomic.com.
- **Result:** **No POST request** appears. Only GET requests are visible (availability, `me`, `en.json`, etc.). So the booking initiation is **not** a simple XHR/fetch POST from the same page. Clicking "Continue - €0.00" performs a **full page navigation** (or new tab) to `app.playtomic.com/payments?type=CUSTOMER_MATCH&tenant_id=...&resource_id=...&start=...&duration=...` – i.e. a payment **page** with query params, not a visible POST in the Network tab on the club page.

---

## Relevant code and config

- **Login / availability:** `src/playtomic_client.py` – `login()`, `fetch_availability()` use **playtomic.com** (WEB_LOGIN_URL, WEB_AVAILABILITY_URL). Session cookies are used.
- **Payment flow:** Same file – `login_playtomic_io()`, `create_payment_intent()`, `update_payment_intent()`, `confirm_reservation()`. Payment base URL is chosen in order: playtomic.io → api.playtomic.io (if web token existed) → app.playtomic.com.
- **Payload shape:** `prepare_payment_intent_data()` builds the cart (CUSTOMER_MATCH, tenant_id, resource_id, start, duration, etc.). `run_booking.py` / reserver use this to find slots and call create → update (select 0 EUR method) → confirm.
- **Config:** `config/booking_config.yaml` (tenants, target_hours, duration, etc.). Credentials from `.env` (PLAYTOMIC_EMAIL, PLAYTOMIC_PASSWORD). See `.env.example`.

---

## What has **not** been tried yet

These are the next directions for whoever continues; no need to re-do the steps above.

1. **HAR (HTTP Archive) capture of full booking flow**  
   Record a **full** browser session (all requests/responses/headers) from “click slot” through “Continue - €0.00” and until the payment page loads (and optionally until confirmation). Export as HAR. Inspect for:
   - Any POST to payment_intents, cart, reservation, or checkout (possibly on app.playtomic.com or another host).
   - Redirects and Set-Cookie that might be required for app.playtomic.com to accept API calls.
   - The exact URL, method, and body that create or load the payment intent.

2. **JavaScript debugging (Sources / Event breakpoints)**  
   In DevTools → Sources, set an **Event Listener Breakpoint** (e.g. click) or a breakpoint on `fetch`/`XMLHttpRequest`. Click "Continue - €0.00" and step through. See which code runs and whether it does a fetch/XHR (and to which URL) or a form submit / `window.location` change. That explains why no POST is visible on the club page.

3. **Capture on the payment page (app.playtomic.com)**  
   Open DevTools **before** clicking "Continue - €0.00". Enable "Preserve log". Click Continue so the app.playtomic.com payment page loads. On **that** page, check the Network tab for any new requests (POST to payment_intents, confirmation, etc.). The creation of the payment intent might happen **on load** of that page (e.g. GET with query params interpreted server-side) or via a POST from that page’s JS.

4. **Mobile app reverse-engineering**  
   If the **mobile app** reliably books 0 EUR slots, capture its traffic (e.g. Charles Proxy, Fiddler, or mitmproxy) and identify the exact host, path, method, headers, and body for creating/confirming a booking. Then mirror that in the bot (if auth can be replicated).

5. **Emulating full page navigation in the bot**  
   If the payment intent is created **server-side** when the user hits `app.playtomic.com/payments?type=CUSTOMER_MATCH&...`, the bot could:
   - Perform a GET (or follow redirects) to that URL with the same cookies/session used for playtomic.com, then
   - Parse the resulting page or subsequent API calls (from a HAR captured on that page) to obtain a payment_intent_id or confirmation token and complete the flow.

---

## Quick reference for next developer

| Goal | Where to look |
|------|----------------|
| How login and availability work | `src/playtomic_client.py` – `login()`, `fetch_availability()` |
| How payment is attempted (and why it fails) | `src/playtomic_client.py` – `create_payment_intent()`, `update_payment_intent()`, `confirm_reservation()`; fallback order and error handling in same file |
| User-facing troubleshooting | `PAYMENT_API_TROUBLESHOOTING.md` |
| Why no POST shows in Network on “Continue” | This file, section “User attempt to capture…” and “What has not been tried yet” (points 1–3, 5) |
| Config and env | `config/booking_config.yaml`, `.env.example`, `src/config.py` |
| Running the bot | `README.md`, `run_booking.py`, `python -m src.scheduler` |

---

## Summary

- **Working:** Login (playtomic.com), availability fetch, slot matching, logic to only book 0 EUR.
- **Not working:** Any of the payment API hosts (playtomic.io, api.playtomic.io, app.playtomic.com) return JSON for payment_intents when called from the bot; app.playtomic.com returns HTML.
- **Blocker:** The exact request that creates the payment intent when a user clicks "Continue - €0.00" was **not** found via Network tab (All or Fetch/XHR) because the action triggers a full page navigation to app.playtomic.com, not a visible POST on the club page.
- **Next:** Use HAR capture, JS debugging, or capture on the payment page / mobile app to find the real request, then align the bot with that (or emulate the navigation and scrape/API-call from there).
