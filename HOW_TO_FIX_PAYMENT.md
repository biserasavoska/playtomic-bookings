# How to fix “Payment API returned HTML”

If the bot logs **"Payment API returned HTML"** or **"Reservation failed (payment API returned HTML)"**, it cannot complete a booking with the current API. To fix it, we need the **exact request** the Playtomic website sends when you book. Do this **once** in your browser.

---

## Steps

1. Open **https://playtomic.com** in **Chrome** or **Firefox** and **log in**.

2. Start a court booking: choose your club, date, time, and go to the step where you see **payment** / **“Book”** / **“Reserve”** / **“Continue”**.

3. Open **Developer Tools**:
   - Press **F12**, or  
   - Right‑click the page → **Inspect**.

4. Go to the **Network** tab.

5. Filter by **Fetch/XHR** (or type `payment`, `intent`, `cart`, `reservation` in the filter box).

6. Click the **clear** (🚫) button so the request list is empty.

7. Click the button that **creates the reservation** (e.g. “Book”, “Pay”, “Confirm”, “Continue - €0.00”).

8. In the Network list, find the **first new request** that appears. It is usually a **POST** and often has a name like `payment_intents`, `cart`, `reservation`, or `checkout`.

9. Click that request. Then copy or note:
   - **Request URL** (e.g. `https://playtomic.com/api/...` or `https://api.playtomic.io/...`)
   - **Request Method** (e.g. POST)
   - **Request Payload**: open the **Payload** or **Request** tab and copy the **JSON body** (or take a screenshot).

10. Send that **URL**, **Method**, and **Payload** (or screenshot). With that, the bot can be updated to use the same endpoint and booking may work.

---

**Full troubleshooting guide:** [PAYMENT_API_TROUBLESHOOTING.md](PAYMENT_API_TROUBLESHOOTING.md) (same folder as this file).
