# Playtomic Auto-Booking

Automated court booking for Playtomic (padel) so your group doesn’t have to race for slots when bookings open. Built on the same approach as [playtomic-scheduler](https://github.com/ypk46/playtomic-scheduler).

**Not technical?** Use **[NEXT_STEPS_GUIDE.md](NEXT_STEPS_GUIDE.md)** for a simple, step-by-step guide (what to click, what to type, where to find things).

## Features

- **Configurable**: Target times (e.g. 18:00–21:30), weekdays only, duration, venue(s)
- **Retries**: Several attempts in quick succession to cover the first seconds after slots open
- **Optional Telegram**: Notify the group when a court is booked or when booking fails
- **GitHub Actions**: Free scheduled runs (e.g. daily at slot release time)
- **Credentials**: Only via environment / secrets; nothing stored in the repo

## Setup

### 1. Python

- Python 3.9 or 3.10+
- Create a venv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Config

- Copy `config/booking_config.yaml` and edit:
  - **tenants**: Your club’s Playtomic venue ID (and optional name). You can get the tenant ID from the Playtomic app or URL when viewing the club.
  - **target_hours**: Start times you want (default 18:00–21:30).
  - **target_weekdays**: 0=Monday … 6=Sunday (default Mon–Fri).
  - **duration_hours**: 1, 1.5, or 2.
  - **booking_release_time** (optional): Local time when slots open (HH:MM). If set, the script can wait until this time before trying.

### 3. Credentials (env only)

- Copy `.env.example` to `.env` and set:
  - `PLAYTOMIC_EMAIL` – your Playtomic login
  - `PLAYTOMIC_PASSWORD` – your Playtomic password
- Never commit `.env`. It’s in `.gitignore`.

### 4. Notifications (optional)

- To get Telegram alerts when a court is booked or booking fails, set in `.env` (or in GitHub Secrets):
  - `TELEGRAM_BOT_TOKEN` – from [@BotFather](https://t.me/BotFather)
  - `TELEGRAM_CHAT_ID` – your group or personal chat ID

## Running

**Local (manual or cron):**

```bash
source .venv/bin/activate
python -m src.scheduler
```

Or:

```bash
python run_booking.py
```

**GitHub Actions:**

1. Push this repo to GitHub.
2. In the repo: **Settings → Secrets and variables → Actions**.
3. Add secrets:
   - `PLAYTOMIC_EMAIL`
   - `PLAYTOMIC_PASSWORD`
   - (Optional) `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
4. Edit `.github/workflows/auto-book.yml`:
   - Set the `schedule` cron to when your club’s slots open (UTC). Example: `55 7 * * 1-5` = 07:55 UTC Mon–Fri. Adjust for your timezone.
5. Workflow runs on schedule; you can also run it manually via **Actions → Playtomic auto-book → Run workflow**.

## Monitoring

- **Logs**: The script logs to stdout (e.g. “Checking venue…”, “Found matching slot…”, “Reservation confirmed…” or errors). In GitHub Actions, check the “Run booking” step log.
- **Telegram**: If configured, you get a message on success or failure.
- **Playtomic app**: Confirm in the app that the reservation appears under your account.

## Finding your tenant ID

1. Open Playtomic (app or web) and go to your club.
2. The venue/club URL or app deep link often contains the tenant ID.
3. Alternatively, use browser dev tools (Network tab) while loading the club page and look for API calls that include a tenant or venue ID.

## Terms and reliability

- This uses the same kind of API calls as the official app (no official public API). Playtomic may change endpoints or rules; automation could break or conflict with their terms of use.
- For time-critical runs, set the GitHub Actions cron so the job starts at or just before when slots open. The script retries several times in the first few seconds to improve the chance of getting a slot.

## Project layout

```
├── config/
│   └── booking_config.yaml   # Venues, times, weekdays, duration
├── src/
│   ├── config.py             # Load config + env credentials
│   ├── playtomic_client.py   # Playtomic API (login, availability, book)
│   ├── reserver.py           # Find matching slots and reserve
│   ├── scheduler.py          # Entry point, retries, optional wait
│   ├── notifications.py     # Optional Telegram
│   └── utils/
├── .github/workflows/
│   └── auto-book.yml         # Scheduled and manual run
├── .env.example
├── requirements.txt
└── README.md
```
