"""Optional notifications (Telegram webhook, email, or log-only)."""
import logging
import os

logger = logging.getLogger(__name__)


def send_notification(title: str, message: str, success: bool = True) -> None:
    """
    Send a notification when a booking succeeds or fails.
    Uses TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID if set; otherwise logs only.
    """
    log_msg = f"{title}: {message}"
    if success:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            _send_telegram(token, chat_id, title, message, success)
        except Exception as e:
            logger.warning("Telegram notification failed: %s", e)


def _send_telegram(token: str, chat_id: str, title: str, message: str, success: bool) -> None:
    """Send a message via Telegram Bot API."""
    import urllib.request
    import urllib.parse
    import json

    text = f"*{title}*\n\n{message}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"Telegram API returned {resp.status}")
