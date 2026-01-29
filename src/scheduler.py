"""
Main booking scheduler: runs at release time with retries for the critical window.
Can be invoked by GitHub Actions or a local cron.
Uses max_attempts + retry_delay to cover the first ~5 seconds after slots open.
"""
import logging
import time
from datetime import datetime
from typing import Optional

import pytz

from .config import (
    load_booking_config,
    get_credentials,
    get_credentials_for_account,
    BookingConfig,
)
from .playtomic_client import PlaytomicClient
from .reserver import Reserver
from .notifications import send_notification
from .utils import date as date_utils

logger = logging.getLogger(__name__)


def _wait_until_release_if_configured(config: BookingConfig) -> None:
    """If booking_release_time is set, sleep until that time (local or in booking_release_timezone)."""
    release = config.booking_release_time
    if not release or ":" not in release:
        return
    try:
        now_utc = datetime.now(pytz.UTC)
        tz_name = getattr(config, "booking_release_timezone", None)
        if tz_name:
            tz = pytz.timezone(tz_name)
            baseline_local = now_utc.astimezone(tz)
            target_local = date_utils.parse_datetime(release.strip(), baseline_local)
            target_utc = target_local.astimezone(pytz.UTC) if target_local.tzinfo else tz.localize(target_local).astimezone(pytz.UTC)
        else:
            # Runner/local clock: naive 08:30 today (e.g. UTC on GitHub Actions)
            target_naive = date_utils.parse_datetime(release.strip(), now_utc.replace(tzinfo=None))
            target_utc = target_naive.replace(tzinfo=pytz.UTC)

        if target_utc > now_utc:
            wait_secs = (target_utc - now_utc).total_seconds()
            if 0 < wait_secs <= 300:  # at most 5 min
                logger.info("Waiting %.0fs until release time %s...", wait_secs, release)
                time.sleep(wait_secs)
    except (ValueError, TypeError, Exception) as e:
        logger.debug("Could not wait until release: %s", e)


def run_booking(
    config: Optional[BookingConfig] = None,
    max_attempts: int = 5,
    retry_delay_seconds: float = 1.0,
    dry_run: bool = False,
) -> bool:
    """
    Load config and credentials, then try to book until success or max_attempts.
    If dry_run=True, only check login and availability; do not book.
    Returns True if a reservation was confirmed (or dry run found a slot).
    """
    config = config or load_booking_config()
    if not dry_run:
        _wait_until_release_if_configured(config)
    if not config.tenants or any(t.id == "YOUR_TENANT_ID" for t in config.tenants):
        logger.error(
            "No valid tenant in config. Set your club's tenant ID in config/booking_config.yaml (see HOW_TO_FIND_TENANT_ID.md)"
        )
        return False

    # Multiple accounts: each has its own credentials and optional overrides (weekdays, accept_any_time, etc.)
    accounts_to_try: list = []
    if getattr(config, "accounts", None):
        accounts_to_try = list(config.accounts)
    if not accounts_to_try:
        # Single account: use PLAYTOMIC_EMAIL / PLAYTOMIC_PASSWORD and main config
        from .config import AccountConfig
        accounts_to_try = [AccountConfig(env_email="PLAYTOMIC_EMAIL", env_password="PLAYTOMIC_PASSWORD", target_weekdays=config.target_weekdays)]

    any_booked = False
    for acc in accounts_to_try:
        try:
            email, password = get_credentials_for_account(acc.env_email, acc.env_password)
        except ValueError as e:
            logger.error("%s", e) if not getattr(config, "accounts", None) else logger.warning("Skip account %s: %s", acc.env_email, e)
            if not getattr(config, "accounts", None) and not dry_run:
                send_notification("Booking failed", str(e), success=False)
            continue

        overrides: dict = {"target_weekdays": acc.target_weekdays}
        if acc.accept_any_time is not None:
            overrides["accept_any_time"] = acc.accept_any_time
        if acc.booking_start_days_ahead is not None:
            overrides["booking_start_days_ahead"] = acc.booking_start_days_ahead
        if acc.booking_days_ahead is not None:
            overrides["booking_days_ahead"] = acc.booking_days_ahead
        account_config = config.model_copy(update=overrides)
        client = PlaytomicClient(email, password)
        try:
            client.login()
        except Exception as e:
            logger.warning("Login failed for account %s: %s", email[:3] + "...", e)
            continue
        # Try playtomic.io login for payment API (Bearer token); if it fails we still use app.playtomic.com
        client.login_playtomic_io()

        reserver = Reserver(client, account_config, dry_run=dry_run)
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
            if reserver.reservation_confirmed or (dry_run and reserver.dry_run_found_slot):
                any_booked = True
                if dry_run:
                    logger.info("[DRY RUN] Found at least one matching slot (see logs above). No booking made.")
                else:
                    send_notification(
                        "Court booked",
                        "A court was successfully reserved via Playtomic. Check the app.",
                        success=True,
                    )
                    logger.info("SUCCESS: A court was booked. Check your Playtomic app.")
                if dry_run:
                    return True
                break
            if attempt < max_attempts:
                time.sleep(retry_delay_seconds)
    if any_booked:
        return True

    if not dry_run:
        send_notification(
            "No court booked",
            f"Tried {max_attempts} times; no matching slot was available or booking failed.",
            success=False,
        )
    if dry_run:
        logger.info("DRY RUN RESULT: No matching slot found for the next 14 days (or tenant ID not set).")
    else:
        logger.info(
            "RESULT: No court was booked (no matching slot found or all were taken). Check logs above."
        )
    return False


def main() -> None:
    """Entry point for CLI or GitHub Actions. Use --dry-run to test without booking."""
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    if dry_run:
        logger.info("Running in DRY RUN mode: will not book, only check login and availability.")
    run_booking(max_attempts=5, retry_delay_seconds=1.0, dry_run=dry_run)


if __name__ == "__main__":
    main()
