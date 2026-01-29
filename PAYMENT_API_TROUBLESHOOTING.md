# Payment / reservation API troubleshooting

The bot can **log in** and **see availability** on Playtomic, but actually **creating a booking** (payment intent → confirm) may fail because Playtomic’s reservation API is not public and can change.

**Current behaviour:**

- The bot **only books when a 0 EUR option is available** (e.g. subscription, included, pay at the club). If the payment intent returns only paid methods (e.g. card, €20), the bot **does not book** and logs a clear message: *"Booking requires payment (€X). Only 0 EUR bookings are automated. Select a 0 EUR option (e.g. subscription, included, pay at the club) in the Playtomic app or book manually."*
- The bot tries **playtomic.io** for the payment API (Bearer token from `api/v3/auth/login`) when that login succeeds; otherwise it uses **app.playtomic.com** (session). If you see "Payment API returned non-JSON" or 403, see below.

---

## Web shows €20 after “Continue - €0.00” (app can book for €0)

**What you found:** On the **mobile app** you can book a slot for **€0** (e.g. with subscription / “Forget the commissions”). On the **web**, when you click **“Continue - €0.00”** on the slot modal, you’re taken to a **different page** that shows **Total €20.00** and “Select a payment method” / “Pay €20.00”.

**What’s likely happening:**

1. **Web and app use the same backend but different requests**  
   When you click “Continue - €0.00”, the web sends a request to create the cart/payment intent. The server may be **not applying your subscription** (or “included” / 0€ option) for that web request, so it returns a €20 total and only paid methods.

2. **The app may send something extra**  
   The app might send an extra parameter, header, or use a different endpoint so the server applies “subscription” / “included” and returns 0€. The web request might be missing that.

**How to confirm and get the exact request:**

1. **Capture the request that creates the cart** (when you click “Continue - €0.00”):
   - Open **DevTools** → **Network**.
   - Filter by **Fetch/XHR** only.
   - Click the **clear** (🚫) button so the list is empty.
   - Click **“Continue - €0.00”** on the slot modal.
   - In the list, find the **first new request** that appears (often a **POST**). That is usually the “create payment intent” or “create cart” call.
   - Click it and copy:
     - **Request URL** (e.g. `https://playtomic.com/api/...` or `https://api.playtomic.io/...`).
     - **Request Method** (e.g. POST).
     - **Request Payload**: In the **Payload** or **Request** tab, copy the JSON body (or a screenshot). That shows what the web sends when it “continues for €0”.

2. **Check the €20 page**  
   On the page that shows “Total €20.00”, click **“Select a payment method”**.  
   - If you see an option like **“Included”**, **“Subscription”**, **“0€”**, or **“Pay at club”**, then the 0€ option exists but the web defaulted to €20.  
   - If you only see card/payment options, then the **create** request did not ask for the 0€ option and we need to change what we send (once we have the real URL and payload from step 1).

If you paste the **URL**, **Method**, and **Payload** (or a screenshot of the Payload) from step 1, we can compare with what the app might send and adjust the bot (or the web flow) so 0€ is requested the same way.

---

**Payment page URL (from “Continue”):**  
When you click “Continue - €0.00”, the payment page opens in a new tab at:

`https://app.playtomic.com/payments?type=CUSTOMER_MATCH&tenant_id=...&resource_id=...&start=YYYY-MM-DDTHH:MM:SS.000Z&duration=90`

So the **payment app** lives on **app.playtomic.com**. The bot tries `https://app.playtomic.com/api/v1/payment_intents` for creating reservations. In practice that URL often returns **HTML** (the web app’s login/app page) instead of JSON, so the payment flow is not a public JSON API: the real booking is done by the browser/SPA, not by a separate API we can call from a script. Until Playtomic exposes a real API or we reverse‑engineer the exact request the SPA sends (e.g. from the browser Network tab when you complete a booking), programmatic booking will keep failing with “Payment API returned non-JSON” or similar.

---

## What you’re seeing (403 / 404 / 405)

| Response | Meaning |
|----------|--------|
| **404**  | That URL doesn’t exist (wrong host or path). |
| **405**  | That URL exists but doesn’t allow POST (wrong path or method). |
| **403**  | That URL exists and allows POST, but the server **rejects our request** (auth or origin). |

With **403**, the usual cause is:

- We log in on **playtomic.com** (session cookies).
- We call **api.playtomic.io** for payment – different domain, so **no cookies** are sent.
- If the web app doesn’t return a Bearer token we can use on api.playtomic.io, that API will respond **403 Forbidden**.

So the “real” booking flow is probably on **playtomic.com** (same domain as login), and we need the **exact URL and method** the browser uses.

## Find the real booking URL (one-time)

1. Open **https://playtomic.com** in Chrome or Firefox and log in.
2. Start a court booking: choose your club, date, time, and go to the step where you see payment / “Book” / “Reserve”.
3. Open **Developer Tools**: `F12` or right‑click → Inspect.
4. Go to the **Network** tab.
5. Filter by **Fetch/XHR** (or type `payment`, `intent`, `cart`, `reservation`, `checkout` in the filter).
6. Click the button that **creates the reservation** (e.g. “Book”, “Pay”, “Confirm”).
7. In the Network list, find the **first** new request that looks like creating a booking (often POST, name like `payment_intents`, `cart`, `reservation`, `checkout`, etc.).
8. Click it and note:
   - **Request URL** (e.g. `https://playtomic.com/api/...` or `https://api.playtomic.io/...`)
   - **Request Method** (e.g. POST)
   - **Request Headers** (optional): Origin, Referer, any custom header.

Send that **URL** and **Method** (and, if possible, a screenshot or copy of the request payload from the “Payload” or “Request” tab). With that, we can point the bot at the same endpoint and, if it’s on playtomic.com, the session cookies from our login will be sent and 403 may be resolved.

## After you have the URL

- If the URL is on **playtomic.com** (e.g. `https://playtomic.com/api/web-app/...`), we’ll switch the payment/reservation calls in the code to that URL so the same session used for login is used for booking.
- If the URL is on **api.playtomic.io** with a different path or required headers, we’ll adjust the client to use that path and headers.

Until then, the bot will keep **finding slots** and **trying to book**; you’ll see 403 (and possibly “Response ended prematurely”) in the logs, but the run will no longer crash and will finish with “No court booked”.
