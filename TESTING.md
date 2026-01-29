# How to test the Playtomic auto-booking

This explains: **cost**, **Playtomic payment**, **where the club and time are set**, **how you know if it worked**, and **how to test** before running on a schedule.

---

## 1. Will I have to pay for GitHub Actions?

**Often no.** GitHub gives you free minutes each month:

- **Private repo** (like yours): **2,000 minutes/month** free.
- Each run of this workflow is about **1–2 minutes** (install + run once).
- If you run it **once per weekday** (e.g. 20 times/month), that’s about **20–40 minutes** – well within the free 2,000.

You only pay if you go over the free tier. GitHub will warn you before charging. You can see usage under: **GitHub → Settings (your profile) → Billing → Plans and usage**.

So you can test and run on schedule without paying, as long as you don’t run hundreds of other workflows.

---

## 2. Do I need to pay Playtomic? What happens with payment?

- **No Playtomic subscription is required** for this bot. It uses your normal Playtomic account (email + password).
- **Payment method:** The bot prefers **“Pay at the club”** when the club offers it. If your club **does not** offer “Pay at the club” (e.g. only “Pay your part” or “Pay everything” by card), the bot uses the **first available method** (e.g. “Pay your part”). So for clubs like 7de Olympiade, the bot will select whatever option the API returns first (typically “Pay your part” or similar); completing the booking may charge your card according to that option. Check the Playtomic app after a run to see the reservation and payment status.

---

## 3. Where does it get the club and preferred time?

Everything is in **one file**: `config/booking_config.yaml` (in your project folder).

| What you want to set | Where in the file |
|----------------------|-------------------|
| **Which club** | Under `tenants:`, set `id: "YOUR_TENANT_ID"` to your club’s Playtomic venue ID (see NEXT_STEPS_GUIDE.md Part 1 to find it). |
| **Preferred time (e.g. 19:00 CET)** | Under `preferred_hours:` we have `"19:00"`. The bot will try **19:00 first**, then other times in `target_hours` if 19:00 is gone. |
| **Other acceptable times** | `target_hours:` lists all start times you accept (18:00–21:30). |
| **Weekdays only** | `target_weekdays: [0,1,2,3,4]` = Mon–Fri. |
| **Duration** | `duration_hours: 1.5` (or 1 or 2). |

So: **club** = tenant `id` in that file; **preferred time** = first entry in `preferred_hours` (19:00).  
**7de Olympiade:** config is already set for that club and preferred order (19:00, then 18:30, 18:00, 19:30, 20:00, 20:30). You only need to replace `YOUR_TENANT_ID` (see **HOW_TO_FIND_TENANT_ID.md**).

---

## 4. How do I know if a court was booked (success or failure)?

| Where | What you see |
|-------|----------------|
| **Telegram** (if you set it up) | A message: “Court booked” + “A court was successfully reserved…” **or** “No court booked” + “Tried X times…”. |
| **GitHub Actions** (when it runs on schedule or manually) | Open the run → **Run booking** step. You’ll see either **“SUCCESS: A court was booked. Check your Playtomic app.”** or **“RESULT: No court was booked…”**. |
| **Playtomic app** | If it worked, a new reservation appears in your Playtomic account (Matches / Reservations). |
| **Terminal** (when you run locally) | Same messages: “SUCCESS: A court was booked…” or “RESULT: No court was booked…”. |

So: **success** = Telegram “Court booked” (if configured) + “SUCCESS” in the log + new reservation in the Playtomic app. **Failure** = “No court booked” / “RESULT: No court was booked” and nothing new in the app.

---

## 5. How to test before using the schedule

You can test in two ways: **on your computer** (safest, no GitHub minutes) and **manually on GitHub** (same as the scheduled run).

### Option A: Dry run (no booking, no payment) – do this first

1. **One-time setup** (if you haven’t already):
   ```bash
   cd ~/Projects/Playtomic\ Bookings
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Set your tenant ID** in `config/booking_config.yaml` (see **HOW_TO_FIND_TENANT_ID.md**).  
3. **Set your credentials** in `.env` (`PLAYTOMIC_EMAIL`, `PLAYTOMIC_PASSWORD`).  
4. Run a dry run (no booking, no charge):
   ```bash
   cd ~/Projects/Playtomic\ Bookings
   source .venv/bin/activate
   python -m src.scheduler --dry-run
   ```
   This will **log in**, **check availability** for the day that is 14 days ahead, and **log which slot it would book** (e.g. “Would book: 2025-02-12 at 19:00”). It **does not** create a reservation or charge anything.

If you see “No valid tenant in config”, replace `YOUR_TENANT_ID` in the config. If you see “Login failed”, check your `.env`.

**Note:** The dry-run and other tests cannot be run from Cursor’s environment (no network). Run the commands above in your own Terminal on your Mac to test.

### Option B: Test on your computer (real booking attempt)

This checks that login, config, and (optionally) a real booking work, without using GitHub.

1. **Set your club and credentials**
   - In `config/booking_config.yaml`: replace `YOUR_TENANT_ID` with your club’s Playtomic venue ID.
   - Ensure you have a `.env` file with `PLAYTOMIC_EMAIL` and `PLAYTOMIC_PASSWORD` (see NEXT_STEPS_GUIDE.md Part 3).

2. **Open Terminal** and go to the project folder:
   ```bash
   cd ~/Projects/Playtomic\ Bookings
   ```

3. **Use a virtual environment and install** (if you haven’t already):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Test that login and config are OK** (no booking):
   ```bash
   python scripts/validate_setup.py
   ```
   You should see “OK: Login successful”. If you see an error, fix the tenant ID or `.env` and try again.

5. **Test a real booking attempt** (this will try to book if a matching slot is available):
   ```bash
   python -m src.scheduler
   ```
   - If **slots are open**: it may book one (preferring 19:00). Check the Playtomic app.
   - If **no slots are open yet**: it will just log that it didn’t find anything. That’s normal.

Once this works on your machine, the same logic runs on GitHub when you trigger the workflow.

---

### Option C: Test with a manual run on GitHub

This runs the **exact same job** as the scheduled one, but you start it by hand. It uses a few minutes of your GitHub Actions quota.

1. **Push your config**  
   Make sure `config/booking_config.yaml` on GitHub has your real **tenant ID** (not `YOUR_TENANT_ID`). If you only have it in the file on your computer, commit and push:
   ```bash
   cd ~/Projects/Playtomic\ Bookings
   git add config/booking_config.yaml
   git commit -m "Set tenant ID for testing"
   git push
   ```

2. **Trigger the workflow by hand**
   - Open your repo on GitHub: **https://github.com/biserasavoska/playtomic-bookings**
   - Click the **Actions** tab.
   - In the left sidebar, click **Playtomic auto-book**.
   - Click **Run workflow** (dropdown) → **Run workflow** (green button).

3. **See the result**
   - After a minute or two, a new run appears. Click it.
   - Click the **book** job, then the **Run booking** step.
   - You’ll see the same kind of log as on your computer (e.g. “Checking venue…”, “Found matching slot…”, “Reservation confirmed” or “No court booked”).

4. **Check Playtomic**  
   If it booked, you’ll see the reservation in the Playtomic app.

---

## 6. When you’re happy with tests

- Leave the **schedule** as it is (07:25 UTC = 08:25 CET, 5 minutes before 08:30).
- The workflow will run **automatically** every weekday at that time.
- You can always run it again by hand from **Actions → Playtomic auto-book → Run workflow**.

---

## Quick checklist before going live

- [ ] `config/booking_config.yaml` has your real **tenant ID** (not `YOUR_TENANT_ID`).
- [ ] `preferred_hours` includes `"19:00"` (already set).
- [ ] You ran `python scripts/validate_setup.py` and saw “OK: Login successful”.
- [ ] You ran `python -m src.scheduler` once (or a manual GitHub run) and saw it try to book.
- [ ] GitHub repo **Secrets** have `PLAYTOMIC_EMAIL` and `PLAYTOMIC_PASSWORD` set.
