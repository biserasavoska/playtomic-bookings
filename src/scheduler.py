"""
Main booking scheduler: runs at release time with retries for the critical window.
Can be invoked by GitHub Actions or a local cron.
Uses max_attempts + retry_delay to cover the first ~5 seconds after slots open.
"""
import logging
import time
from datetime import datetime
from typing import Optional

from .config import load_booking_config, get_credentials, BookingConfig
from .playtomic_client import PlaytomicClient
from .reserver import Reserver
from .notifications import send_notification
from .utils import date as date_utils

logger = logging.getLogger(__name__)


def _wait_until_release_if_configured(config: BookingConfig) -> None:
    """If booking_release_time is set, sleep until that time (local) today."""
    release = config.booking_release_time
    if not release or ":" not in release:
        return
    now = datetime.now()
    try:
        target = date_utils.parse_datetime(release.strip(), now)
        if target > now:
            wait_secs = (target - now).total_seconds()
            if 0 < wait_secs <= 300:  # at most 5 min
                logger.info("Waiting %.0fs until release time %s...", wait_secs, release)
                time.sleep(wait_secs)
    except (ValueError, TypeError):
        pass


def run_booking(
    config: Optional[BookingConfig] = None,
    max_attempts: int = 5,
    retry_delay_seconds: float = 1.0,
) -> bool:
    """
    Load config and credentials, then try to book until success or max_attempts.
    Returns True if a reservation was confirmed.
    """
    config = config or load_booking_config()
    _wait_until_release_if_configured(config)
    if not config.tenants:
        logger.error("No tenants in config. Add at least one venue (tenant id) in config/booking_config.yaml")
        return False

    try:
        email, password = get_credentials()
    except ValueError as e:
        logger.error("%s", e)
        send_notification("Booking failed", str(e), success=False)
        return False

    client = PlaytomicClient(email, password)
    try:
        client.login()
    except Exception as e:
        logger.exception("Login failed: %s", e)
        send_notification("Playtomic login failed", str(e), success=False)
        return False

    reserver = Reserver(client, config)
    for attempt in range(1, max_attempts + 1):
        if reserver.reservation_confirmed:
            break
        reserver.client.login()
        for tenant in config.tenants:
            if reserver.reservation_confirmed:
                break
            reserver.process_tenant(
                tenant.id,
                tenant.name,
                reservations_per_week=config.reservations_per_week,
            )
        if reserver.reservation_confirmed:
            send_notification(
                "Court booked",
                "A court was successfully reserved via Playtomic.",
                success=True,
            )
            return True
        if attempt < max_attempts:
            time.sleep(retry_delay_seconds)

    send_notification(
        "No court booked",
        f"Tried {max_attempts} times; no matching slot was available or booking failed.",
        success=False,
    )
    return False


def main() -> None:
    """Entry point for CLI or GitHub Actions."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_booking(max_attempts=5, retry_delay_seconds=1.0)


if __name__ == "__main__":
    main()
