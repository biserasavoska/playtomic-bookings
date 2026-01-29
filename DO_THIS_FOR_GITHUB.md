# GitHub setup – do this once (in your Terminal and on GitHub)

Cursor can’t run `git init` or push to GitHub from here, and **only you** can add your password as a Secret on GitHub. Follow these steps once.

---

## Step 1: Open Terminal on your Mac

1. Press **Cmd + Space**, type **Terminal**, press Enter.
2. In Terminal, go to your project folder. Copy and paste this, then press Enter:

   ```bash
   cd ~/Projects/Playtomic\ Bookings
   ```

---

## Step 2: Turn this folder into a Git repo and make the first commit

Copy and paste **each block** below, one at a time, and press Enter after each.

**Block 1 – start Git:**
```bash
git init
```

**Block 2 – add all files:**
```bash
git add -A
```

**Block 3 – first commit:**
```bash
git commit -m "Initial setup - Playtomic auto-booking"
```

If you see “nothing to commit” or “no changes”, that’s fine – it might mean everything was already committed. Continue to Step 3.

---

## Step 3: Create a new repo on GitHub (in the browser)

1. Open **https://github.com/new** in your browser.
2. Log in if asked.
3. **Repository name:** type e.g. **playtomic-bookings** (or any name you like).
4. Choose **Private** (recommended).
5. **Do not** tick “Add a README” or “Add .gitignore” – you already have them.
6. Click **Create repository**.

---

## Step 4: Connect your folder to GitHub and push

GitHub will show a page like “…or push an existing repository from the command line.” Use the **HTTPS** URL it shows (looks like `https://github.com/YOUR_USERNAME/playtomic-bookings.git`).

In Terminal, run these two commands. **Replace the URL** with the one GitHub shows you.

**Block 1 – link this folder to GitHub:**
```bash
git remote add origin https://github.com/YOUR_USERNAME/playtomic-bookings.git
```
(Change `YOUR_USERNAME` and `playtomic-bookings` to your real GitHub username and repo name.)

**Block 2 – send your code to GitHub:**
```bash
git branch -M main && git push -u origin main
```

If it asks for your **GitHub username and password**:  
- Use your GitHub **username**.  
- For password, use a **Personal Access Token** (GitHub no longer accepts account passwords here).  
  - To create one: GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token**. Give it a name, tick **repo**, then generate and copy the token. Paste it when Terminal asks for a password.

After a successful push, your code is on GitHub.

---

## Step 5: Add your Playtomic email and password as Secrets (only in the browser)

Only you can do this, because only you should know your password.

1. On GitHub, open **your repository** (e.g. **github.com/YOUR_USERNAME/playtomic-bookings**).
2. Click **Settings** (top tab of the repo).
3. In the left sidebar, click **Secrets and variables** → **Actions**.
4. Click **“New repository secret”**.
5. Add **two** secrets:

   | Name                 | Value              |
   |----------------------|--------------------|
   | **PLAYTOMIC_EMAIL**   | Your Playtomic login email |
   | **PLAYTOMIC_PASSWORD** | Your Playtomic password   |

   For each: type the **Name** exactly as in the table, then paste or type the **Value**, then click **Add secret**.

After this, the automatic booking workflow can run using your account.

---

## Step 6: Set the time when bookings open (optional)

The workflow runs on **GitHub’s clock (UTC)**. You want it to run about **5 minutes before** your club opens bookings in *your* local time.

### What to do

1. On GitHub, open your repo → click the file **.github/workflows/auto-book.yml** → click the **pencil icon** (Edit).
2. Find the line that starts with `- cron: "…"` (under `schedule:`).
3. **Replace it** with the line from the table below that matches when your club opens bookings (Monday–Friday only). Default is 8:30 CET: `- cron: "25 7 * * 1-5"`.

### Pick your time (copy one line into the file)

| Club opens at (your local time) | Your timezone | Replace with this cron line |
|--------------------------------|---------------|-----------------------------|
| **8:30** in the morning        | Belgium/Netherlands (CET) | `- cron: "25 7 * * 1-5"` *(default)* |
| **8:00** in the morning        | Spain (winter CET)  | `- cron: "55 6 * * 1-5"` |
| **8:00** in the morning        | Spain (summer CEST) | `- cron: "55 5 * * 1-5"` |
| **9:00** in the morning       | Spain (winter CET)  | `- cron: "55 7 * * 1-5"` |
| **9:00** in the morning       | Spain (summer CEST) | `- cron: "55 6 * * 1-5"` |
| **8:00** in the morning       | UK (winter GMT)     | `- cron: "55 7 * * 1-5"` |
| **8:00** in the morning       | UK (summer BST)     | `- cron: "55 6 * * 1-5"` |
| **9:00** in the morning       | UK (winter GMT)     | `- cron: "55 8 * * 1-5"` |
| **9:00** in the morning       | UK (summer BST)     | `- cron: "55 7 * * 1-5"` |
| **7:00** in the morning       | Spain (winter CET)  | `- cron: "55 5 * * 1-5"` |
| **7:00** in the morning       | Spain (summer CEST) | `- cron: "55 4 * * 1-5"` |

- **Winter** = roughly October–March. **Summer** = roughly April–September (when clocks go forward).
- Not in the table? Your time is “X:00” in timezone “T”: convert X:00 to UTC (subtract 1 hour for CET, 2 for CEST, 0 for GMT, etc.). Then use **5 minutes before** that UTC time. Format: `"55 (UTC hour minus 1) * * 1-5"` (e.g. 8:00 UTC → run at 07:55 UTC → `"55 7 * * 1-5"`).

4. Click **Commit changes** (green button).

---

## How the automated run works (e.g. tomorrow at 8:30 CET)

1. **GitHub wakes the job** at **07:25 UTC** (08:25 CET), Monday–Friday. That’s 5 minutes *before* your club opens bookings at 08:30 CET.
2. **The workflow** checks out the repo, installs Python and dependencies, then runs `python -m src.scheduler`.
3. **The scheduler** reads `booking_release_time` and `booking_release_timezone` from `config/booking_config.yaml`. It **waits** until **08:30 Europe/Brussels** (CET), then starts trying to book.
4. **Booking** runs up to 5 times with a 1-second pause between attempts, so you hit the first few seconds after slots open.
5. **Result**: If a matching slot is found (e.g. 19:00 on a weekday in the next 14 days), the court is reserved and you get a Telegram notification (if configured). Otherwise you get a “No court booked” notification.

To run it once by hand: **Actions** → **Playtomic auto-book** → **Run workflow**.

---

## Done

- Your code is on GitHub.
- Your email and password are stored as Secrets (only the workflow can use them).
- The workflow will run at the time you set (or the default 07:55 UTC weekdays).

To run it once by hand: go to the **Actions** tab → **Playtomic auto-book** → **Run workflow**.

If anything in Step 2 or 4 fails, copy the error message and you can look it up or ask for help with that exact message.
