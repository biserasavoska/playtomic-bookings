"""Reservation logic: fetch availability, filter by config, book court."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from requests.exceptions import ChunkedEncodingError, HTTPError, RequestException

from .config import BookingConfig
from .playtomic_client import PlaytomicClient
from .utils import date

logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Stop trying more slots after this many failed reservation attempts (so we don't run for minutes)
MAX_RESERVATION_FAILURES = 3

# Names/patterns that indicate a 0 EUR option (subscription, included, pay at club, etc.)
ZERO_EUR_INDICATORS = (
    "included",
    "subscription",
    "member",
    "0 €",
    "0 eur",
    "0€",
    "pay at the club",
    "pay at club",
)


def _is_zero_eur_method(method: Dict[str, Any]) -> bool:
    """True if this payment method is a 0 EUR option (no card/payment required)."""
    name = (method.get("name") or "").strip().lower()
    if any(x in name for x in ZERO_EUR_INDICATORS):
        return True
    amount = method.get("amount") or method.get("total") or method.get("price")
    if amount is not None and (amount == 0 or (isinstance(amount, (int, float)) and float(amount) == 0)):
        return True
    return False


def _payment_required_message(payment_intent: Dict[str, Any]) -> str:
    """Build a clear message when booking requires payment (not 0 EUR)."""
    amount = (
        payment_intent.get("total_amount")
        or payment_intent.get("amount")
        or payment_intent.get("total")
        or payment_intent.get("price")
    )
    if amount is not None:
        try:
            amt = float(amount)
            currency = payment_intent.get("currency") or "EUR"
            amount_str = f"{amt:.2f} {currency}".replace(".00", "")
        except (TypeError, ValueError):
            amount_str = str(amount)
    else:
        amount_str = "a non-zero amount"
    return (
        f"Booking requires payment ({amount_str}) and a payment method. "
        "Only 0 EUR bookings are automated. "
        "Select a 0 EUR option (e.g. subscription, included, pay at the club) in the Playtomic app or book manually."
    )


class Reserver:
    """Finds and reserves courts matching config (days, hours, duration)."""

    def __init__(
        self,
        client: PlaytomicClient,
        config: BookingConfig,
        dry_run: bool = False,
    ) -> None:
        self.client = client
        self.config = config
        self.dry_run = dry_run
        self.reservation_confirmed = False
        self.dry_run_found_slot = False
        self._reservation_failures = 0

    def _target_dates_for_day(self, base_date: datetime) -> List[datetime]:
        """Parse target hour strings into datetimes for the given day."""
        return [
            date.parse_datetime(h.strip(), base_date)
            for h in self.config.target_hours
        ]

    def _slot_matches_target(self, slot_start: datetime) -> bool:
        """Check if slot matches target weekday and (unless accept_any_time) target hours."""
        if self.config.weekdays_only and slot_start.weekday() not in self.config.target_weekdays:
            return False
        if getattr(self.config, "accept_any_time", False):
            return True
        base = slot_start.replace(hour=0, minute=0, second=0, microsecond=0)
        targets = self._target_dates_for_day(base)
        return any(
            slot_start.hour == t.hour and slot_start.minute == t.minute
            for t in targets
        )

    def process_tenant(self, tenant_id: str, tenant_name: str, reservations_per_week: int = 1) -> None:
        """Check availability for one venue and book if a matching slot is found."""
        logger.info("Checking venue %s (%s)...", tenant_name or tenant_id, tenant_id)
        self._reservation_failures = 0

        week_matches = 0
        try:
            matches = self.client.get_matches(10, "start_date,desc")
            for match in matches:
                if match.get("status") != "PENDING":
                    continue
                start_str = match.get("start_date")
                if not start_str:
                    continue
                match_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S")
                match_dt = date.parse_utc_to_local(match_dt)
                if date.is_within_current_week(match_dt):
                    week_matches += 1
        except Exception as e:
            logger.warning("Could not fetch matches: %s", e)

        today = date.set_start_of_day(datetime.now())
        days_ahead = getattr(self.config, "booking_days_ahead", 14)
        start_offset = getattr(self.config, "booking_start_days_ahead", None)
        if start_offset is not None:
            # Per-account: e.g. 0 = search from today through today+days_ahead
            start_date = today + timedelta(days=start_offset)
            search_limit = today + timedelta(days=days_ahead)
        else:
            if week_matches >= reservations_per_week:
                start_date = today + timedelta(days=7 - today.weekday())
            else:
                start_date = today + timedelta(days=days_ahead)
            search_limit = today + timedelta(days=min(21, days_ahead + 7))
        end_date = date.set_end_of_day(start_date)

        while start_date < search_limit and not self.reservation_confirmed:
            if self._reservation_failures >= MAX_RESERVATION_FAILURES:
                break
            try:
                entries = self.client.fetch_availability(tenant_id, start_date, end_date)
            except HTTPError as err:
                logger.warning("Availability fetch failed for %s: %s", start_date.date(), err)
                start_date += timedelta(days=1)
                end_date += timedelta(days=1)
                continue

            logger.info("Checking availability for %s...", start_date.strftime("%Y-%m-%d"))
            for entry in entries:
                if self._reservation_failures >= MAX_RESERVATION_FAILURES:
                    break
                self._process_availability_entry(entry, tenant_id)

            start_date += timedelta(days=1)
            end_date += timedelta(days=1)

        if self._reservation_failures >= MAX_RESERVATION_FAILURES and not self.reservation_confirmed:
            logger.warning(
                "Stopped trying more dates after %d failed reservation attempts for this venue.",
                MAX_RESERVATION_FAILURES,
            )

    def _preferred_rank(self, slot_start: datetime) -> int:
        """Lower = more preferred. Slots matching preferred_hours get 0."""
        if not self.config.preferred_hours:
            return 0
        key = slot_start.strftime("%H:%M")
        for i, h in enumerate(self.config.preferred_hours):
            if h.strip() == key:
                return i
        return len(self.config.preferred_hours)

    def _process_availability_entry(self, entry: Dict[str, Any], tenant_id: str) -> None:
        """Process one availability entry (one resource/date). Try preferred times first."""
        resource_id = entry.get("resource_id")
        start_date_str = entry.get("start_date")
        slots = entry.get("slots") or []
        duration_minutes = int(self.config.duration_hours * 60)

        matches: List[tuple] = []
        for slot in slots:
            if slot.get("duration") != duration_minutes:
                continue
            slot_time = slot.get("start_time")
            if not slot_time or not start_date_str:
                continue
            slot_start_str = f"{start_date_str} {slot_time}"
            try:
                slot_start = datetime.strptime(slot_start_str, DATE_FORMAT)
            except ValueError:
                continue
            slot_start = date.parse_utc_to_local(slot_start.replace(tzinfo=None))

            if not self._slot_matches_target(slot_start):
                continue
            matches.append((self._preferred_rank(slot_start), resource_id, slot_start))

        matches.sort(key=lambda x: (x[0], x[2]))
        for _, rid, slot_start in matches:
            if self.reservation_confirmed:
                break
            if self._reservation_failures >= MAX_RESERVATION_FAILURES:
                break
            readable = slot_start.strftime("%Y %b %d - %H:%M")
            logger.info("Found matching slot: %s", readable)
            self._reserve_court(tenant_id, rid, slot_start)
            if not self.reservation_confirmed and not self.dry_run:
                self._reservation_failures += 1

    def _reserve_court(self, tenant_id: str, resource_id: str, start_date: datetime) -> None:
        """Create payment intent, select payment method, confirm reservation (or log only if dry_run)."""
        if self.dry_run:
            self.dry_run_found_slot = True
            logger.info(
                "[DRY RUN] Would book: %s at %s (tenant=%s, resource=%s)",
                start_date.strftime("%Y-%m-%d"),
                start_date.strftime("%H:%M"),
                tenant_id,
                resource_id,
            )
            return
        duration_minutes = int(self.config.duration_hours * 60)
        data = self.client.prepare_payment_intent_data(
            tenant_id, resource_id, start_date, duration_minutes
        )
        try:
            payment_intent = self.client.create_payment_intent(data)
        except ValueError as e:
            logger.error("Reservation failed (payment API returned HTML): %s", e)
            return
        except ChunkedEncodingError as e:
            logger.warning("Reservation failed: server closed connection (%s). Try again.", e)
            return
        except RequestException as e:
            logger.warning("Reservation failed: %s", e)
            return
        except HTTPError as err:
            if err.response is not None and err.response.status_code == 403:
                logger.error(
                    "Reservation failed: 403 Forbidden. The payment API rejects our request (auth/domain). "
                    "See PAYMENT_API_TROUBLESHOOTING.md to find the real booking URL from your browser."
                )
            else:
                logger.exception(
                    "Reservation failed: %s %s",
                    getattr(err.response, "status_code", ""),
                    getattr(err.response, "text", ""),
                )
            return
        try:
            methods = payment_intent.get("available_payment_methods") or []
            zero_eur_methods = [m for m in methods if _is_zero_eur_method(m)]
            if not zero_eur_methods:
                msg = _payment_required_message(payment_intent)
                logger.error("SKIP (payment required): %s", msg)
                return
            selected = zero_eur_methods[0]
            logger.info("Using 0 EUR payment method: %s", selected.get("name") or "0 EUR option")
            self.client.update_payment_intent(
                payment_intent["payment_intent_id"],
                {
                    "selected_payment_method_id": selected.get("payment_method_id"),
                    "selected_payment_method_data": None,
                },
            )
            self.client.confirm_reservation(payment_intent["payment_intent_id"])
            logger.info("Reservation confirmed: %s", start_date.strftime("%Y %b %d - %H:%M"))
            self.reservation_confirmed = True
        except ChunkedEncodingError:
            logger.warning("Reservation failed: server closed connection. Try again.")
        except RequestException as e:
            logger.warning("Reservation failed: %s", e)
        except HTTPError as err:
            logger.exception(
                "Reservation failed: %s %s",
                getattr(err.response, "status_code", ""),
                getattr(err.response, "text", ""),
            )
