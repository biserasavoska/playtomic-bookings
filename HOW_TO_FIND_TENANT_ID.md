# How to find your club’s Playtomic tenant ID

The bot needs your club’s **tenant ID** (a UUID like `a1b2c3d4-e5f6-7890-abcd-ef1234567890`). Playtomic doesn’t show it on the page, so you get it from the browser.

## Steps (about 2 minutes)

1. Open your club on Playtomic in a browser:  
   **https://playtomic.com/clubs/zuid-antwerp-padelclub-7de-olympiade**
2. Open **Developer Tools**:  
   - **Mac:** `Cmd + Option + I` or right‑click → **Inspect**  
   - **Windows:** `F12` or `Ctrl + Shift + I`
3. Go to the **Network** tab.
4. Reload the page (`F5` or `Cmd + R`).
5. In the filter box, type **availability** or **tenant**.
6. Click one of the requests that contains **availability** or **tenant_id** in the URL.
7. In the **Headers** or **Request URL** section, find **tenant_id=** in the URL.  
   The value after it (letters, numbers, and hyphens) is your tenant ID.
8. Copy it and paste it into **config/booking_config.yaml** where it says `YOUR_TENANT_ID`.

Example URL:  
`https://playtomic.io/api/v1/availability?...&tenant_id=a1b2c3d4-e5f6-7890-abcd-ef1234567890`  
→ Tenant ID: **a1b2c3d4-e5f6-7890-abcd-ef1234567890**
