# Notifications: “Court booked” and “No court booked”

When the bot runs (on schedule or when you run it by hand), you can get a **short message** when:
- a court was **booked** (“Court booked – A court was successfully reserved…”), or  
- **no court was booked** (“No court booked – Tried X times…”).

Right now the only option built in is **Telegram**. There is **no WhatsApp** option in this project.

---

## What is Telegram?

**Telegram** is a free messaging app (like WhatsApp). You can install it on your phone or use the web version. The bot doesn’t need you to chat with it; it just **sends one message** to you (or a group) when a booking succeeds or fails.

- **Why Telegram and not WhatsApp?**  
  WhatsApp doesn’t offer a free, simple API for personal bots. Telegram does: you create a small “bot”, get a token, and the script sends a message to your chat. So in this project, notifications are **Telegram only**. Alternatives would be **email** (we could add that later) or **no notification** (you only check the GitHub Actions log or the Playtomic app).

---

## How to set up Telegram notifications (optional)

If you don’t set this up, the bot still runs; you just won’t get a push message. You can always check the **GitHub Actions** run or the **Playtomic app** to see if something was booked.

### Step 1: Install Telegram

On your phone: install **Telegram** from the App Store / Google Play. Or use the web version: https://web.telegram.org

### Step 2: Create a bot and get the token

1. In Telegram, search for **@BotFather**.
2. Start a chat and send: **`/newbot`**.
3. Follow the prompts: choose a name (e.g. “Playtomic Booker”) and a username (e.g. `my_playtomic_booker_bot`). It must end in `bot`.
4. BotFather will reply with a **token** that looks like:  
   `123456789:ABCdefGHIjkLmnoPQRstuVwXyz`
5. **Copy that token** and keep it secret (like a password).

### Step 3: Get your chat ID

1. In Telegram, search for **@userinfobot** (or another “get my id” bot).
2. Start the chat; it will reply with your **user ID** (a number, e.g. `987654321`).
3. **Copy that number**; this is your **chat ID** for private messages to you.

(If you want the message in a **group**, you’d use the group’s chat ID instead; that’s a negative number and requires adding the bot to the group first.)

### Step 4: Give the script the token and chat ID

**On your computer (when you run the script locally):**  
In your **`.env`** file (same folder as the project), add two lines (use your real token and chat ID):

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjkLmnoPQRstuVwXyz
TELEGRAM_CHAT_ID=987654321
```

**On GitHub (when the bot runs on schedule):**  
In your repo: **Settings → Secrets and variables → Actions → New repository secret.**  
Create two secrets:

- **Name:** `TELEGRAM_BOT_TOKEN`  **Value:** (paste your token)
- **Name:** `TELEGRAM_CHAT_ID`    **Value:** (paste your chat ID, e.g. `987654321`)

After that, when the workflow runs, it will send a Telegram message when a court is booked or when no court was booked.

---

## WhatsApp instead of Telegram?

**Not in this project.** WhatsApp doesn’t provide a free, simple API for personal “send one message” bots. To use WhatsApp you’d need something like WhatsApp Business API (paid) or a third-party service. So the only built-in option here is **Telegram**. If you prefer not to use Telegram, you can skip notifications and just check the **GitHub Actions** log and the **Playtomic app** to see if a court was booked.
