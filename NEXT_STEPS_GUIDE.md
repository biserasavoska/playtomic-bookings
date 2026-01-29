# Your step-by-step guide to finish the Playtomic auto-booking

This guide is for non-technical users. Follow the steps in order. If something is unclear, you can ask for help.

---

## What you’ll need before starting

- Your **Playtomic login email** and **password**
- A **computer** where you can open files and run a couple of commands (or use GitHub in the browser)
- (Optional) **Telegram** – if you want a message when a court is booked or when it fails

---

## Part 1: Find your club’s “tenant ID” (venue ID)

The program needs to know **which club** to book at. Playtomic calls this the “tenant ID”. You need to find it once.

### Option A: From the Playtomic website (easiest)

1. Open your browser and go to **https://playtomic.io**
2. Log in with your Playtomic account.
3. Go to **your club’s page** (the one you always book at).
4. Look at the **address bar** at the top. The URL might look like:
   - `https://playtomic.io/tenants/ABC123XYZ/...`  
   or  
   - `https://playtomic.io/...?tenant=ABC123XYZ`
5. The part that looks like **ABC123XYZ** (letters and numbers) is your **tenant ID**.  
   Copy it and keep it somewhere (e.g. a Note). You’ll paste it in Part 2.

### Option B: If you can’t see it in the URL

1. On the club’s page, right‑click and choose **“Inspect”** or **“Inspect element”** (or press F12).
2. Click the **“Network”** tab.
3. Refresh the page (F5).
4. In the list of requests, click one that says something like **“availability”** or **“tenant”**.
5. In the details, look for a field like **tenant_id** or **tenantId**. The value next to it is your tenant ID.

If this is too technical, ask a tech-savvy friend or try Option A first.

---

## Part 2: Tell the program which club and times to use

1. On your computer, go to the project folder: **Playtomic Bookings**.
2. Open the **config** folder.
3. Open the file **booking_config.yaml** in a text editor (Notepad, TextEdit, or VS Code).
4. Find this block (near the bottom):

   ```yaml
   tenants:
     - id: "YOUR_TENANT_ID"   # Replace with your club's Playtomic venue ID
       name: "My Padel Club"
   ```

5. **Replace** `YOUR_TENANT_ID` with the tenant ID you found in Part 1.  
   Example: if your ID is `abc123xyz`, it should look like:

   ```yaml
   tenants:
     - id: "abc123xyz"
       name: "My Padel Club"
   ```

6. (Optional) Change **name** to your club’s real name – it’s only for the logs.
7. **Save** the file and close it.

The rest of the file (times 18:00–21:30, weekdays, 1.5 hours) is already set for your group. You can leave it as is.

---

## Part 3: Add your Playtomic password safely (never in the code)

The program needs your Playtomic email and password to book for you. These must go in a **separate file** that is never shared or uploaded.

1. In the **Playtomic Bookings** folder, find the file **.env.example**.
2. **Duplicate** it (copy–paste or “Save as”) and name the copy **.env** (exactly, with the dot at the start).
3. Open **.env** in a text editor.
4. You’ll see lines like:

   ```
   PLAYTOMIC_EMAIL=your@email.com
   PLAYTOMIC_PASSWORD=your_password
   ```

5. **Replace** with your real details:
   - After `PLAYTOMIC_EMAIL=` type your Playtomic email (no spaces).
   - After `PLAYTOMIC_PASSWORD=` type your Playtomic password (no spaces).

   Example:

   ```
   PLAYTOMIC_EMAIL=maria@gmail.com
   PLAYTOMIC_PASSWORD=MySecretPass123
   ```

6. **Save** the file and close it.
7. **Important:** Never share the **.env** file or put it on GitHub. The project is already set up to ignore it.

---

## Part 4: Run the program on your computer (test once)

Do this once to check that everything works before you set up automatic runs.

### 4.1 Open a “terminal” (command line)

- **Mac:** Open “Terminal” (search for “Terminal” in Spotlight).
- **Windows:** Open “Command Prompt” or “PowerShell” (search for “cmd” or “PowerShell”).

### 4.2 Go to the project folder

Type this (replace with your real path if different):

- **Mac / Linux:**  
  `cd ~/Projects/Playtomic\ Bookings`

- **Windows:**  
  `cd C:\Users\YourName\Projects\Playtomic Bookings`

Press Enter.

### 4.3 Create a “virtual environment” and install the program (one time)

Copy and paste these commands **one by one**, pressing Enter after each:

```bash
python3 -m venv .venv
```

Then:

- **Mac / Linux:**  
  `source .venv/bin/activate`

- **Windows:**  
  `.venv\Scripts\activate`

Then:

```bash
pip install -r requirements.txt
```

Wait until it finishes without errors.

### 4.4 Check that setup is correct (no booking yet)

Run:

```bash
python scripts/validate_setup.py
```

You should see messages like “OK: Login successful”. If you see “ERROR”, read the message – it usually says what’s wrong (e.g. wrong password, or tenant ID missing in config).

### 4.5 Try a real booking (optional but recommended)

When you’re ready to try booking once:

```bash
python -m src.scheduler
```

This will try to book according to your config. Check your Playtomic app or email to see if a court was reserved. If slots aren’t open yet, the program will just say it didn’t find anything – that’s normal.

---

## Part 5: Make it run automatically every day (GitHub Actions)

So you don’t have to run the program yourself each morning, you can let **GitHub** run it for you at a set time (e.g. when your club opens bookings).

### 5.1 Put your project on GitHub

1. Create an account at **https://github.com** if you don’t have one.
2. Create a **new repository** (button “New repository”).
   - Name it e.g. **playtomic-bookings**.
   - Choose **Private** if you don’t want others to see the code.
   - Don’t add a README or .gitignore (you already have them).
3. Open Terminal again in your **Playtomic Bookings** folder and run:

   ```bash
   git init
   git add .
   git commit -m "Initial setup"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/playtomic-bookings.git
   git push -u origin main
   ```

   Replace **YOUR_USERNAME** and **playtomic-bookings** with your GitHub username and repo name.  
   If you’re asked to log in, use your GitHub account (or a “Personal Access Token” if you use 2FA).

### 5.2 Add your password and email as “Secrets” (so GitHub can log in for you)

1. On GitHub, open **your repository** (playtomic-bookings).
2. Click **Settings** (top menu of the repo).
3. In the left sidebar, click **Secrets and variables** → **Actions**.
4. Click **“New repository secret”**.
5. Create these **four secrets** (one by one):

   | Name                 | Value              | Where to get it                    |
   |----------------------|--------------------|------------------------------------|
   | PLAYTOMIC_EMAIL      | your@email.com     | Your Playtomic login email         |
   | PLAYTOMIC_PASSWORD   | YourPassword       | Your Playtomic password             |
   | TELEGRAM_BOT_TOKEN   | (optional)         | From Telegram @BotFather, if you use Telegram |
   | TELEGRAM_CHAT_ID     | (optional)         | Your or group chat ID, if you use Telegram    |

   For each: **Name** = exactly as in the table (copy‑paste). **Value** = your real email/password.  
   You can skip the two TELEGRAM_ ones if you don’t use Telegram.

### 5.3 Set the time when bookings open (cron)

The program is set to run at **07:55 UTC** on weekdays. You need to change this to **your** club’s time.

1. In your repo on GitHub, open the file: **.github/workflows/auto-book.yml**.
2. Click the **pencil icon** (Edit).
3. Find the line that looks like:

   ```yaml
   - cron: "55 7 * * 1-5"
   ```

4. **Cron format:** `minute hour * * day-of-week`
   - Minute: 0–59  
   - Hour: 0–23 (in **UTC**)  
   - Day: 1–5 = Monday–Friday  

   **Example:** If your club opens bookings at **8:00 in the morning** in **Spain (CET/CEST)**:
   - In winter (CET = UTC+1): 8:00 CET = 7:00 UTC → use `0 7 * * 1-5` (run at 07:00 UTC).
   - In summer (CEST = UTC+2): 8:00 CEST = 6:00 UTC → use `0 6 * * 1-5` (run at 06:00 UTC).

   So you might set: **5 minutes before** that time, e.g. `55 6 * * 1-5` for 06:55 UTC (≈ 08:55 CEST).

5. **Save** the file (button “Commit changes”).

From now on, GitHub will run the booking script at that time every weekday. You can also run it manually: **Actions** → **Playtomic auto-book** → **Run workflow**.

---

## Part 6: Check that it worked

- **Right after setup:** Run **Part 4.4** and **4.5** on your computer to confirm login and one booking attempt.
- **After enabling GitHub Actions:** The next day, go to **Actions** in your repo and open the latest “Playtomic auto-book” run. Check the **“Run booking”** step: it will show the same kind of messages as when you ran it locally (e.g. “Checking venue…”, “Reservation confirmed” or “No court booked”).
- **In the app:** Open Playtomic and see if a new reservation appeared.
- **Telegram:** If you added the Telegram secrets, you’ll get a message when a court is booked or when the run fails.

---

## Quick checklist

Before you consider everything “finalised”, make sure:

- [ ] **Part 1:** You found and copied your club’s tenant ID.
- [ ] **Part 2:** In `config/booking_config.yaml` you replaced `YOUR_TENANT_ID` with that ID and saved.
- [ ] **Part 3:** You created a `.env` file (from `.env.example`) and put your real Playtomic email and password in it; you did **not** commit or upload `.env`.
- [ ] **Part 4:** You ran `python scripts/validate_setup.py` and saw “OK: Login successful”, and (optionally) ran `python -m src.scheduler` once.
- [ ] **Part 5:** You pushed the project to GitHub, added **PLAYTOMIC_EMAIL** and **PLAYTOMIC_PASSWORD** as repository Secrets, and edited the **cron** in `.github/workflows/auto-book.yml` to your club’s booking-open time (UTC).
- [ ] **Part 6:** You know where to look (Actions → last run → “Run booking”) to see if the automatic booking ran and whether it succeeded.

If you want, the next step can be a one-page “troubleshooting” with the most common errors (wrong tenant ID, wrong password, cron time) and what to do for each.
