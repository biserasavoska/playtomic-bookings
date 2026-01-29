"""Reservation logic: fetch availability, filter by config, book court."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from requests.exceptions import HTTPError

from .config import BookingConfig
from .playtomic_client import PlaytomicClient
from .utils import date

logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class Reserver:
    """Finds and reserves courts matching config (days, hours, duration)."""

    def __init__(
        self,
        client: PlaytomicClient,
        config: BookingConfig,
    ) -> None:
        self.client = client
        self.config = config
        self.reservation_confirmed = False

    def _target_dates_for_day(self, base_date: datetime) -> List[datetime]:
        """Parse target hour strings into datetimes for the given day."""
        return [
            date.parse_datetime(h.strip(), base_date)
            for h in self.config.target_hours
        ]

    def _slot_matches_target(self, slot_start: datetime) -> bool:
        """Check if slot start time matches one of our target hours and weekday."""
        if self.config.weekdays_only and slot_start.weekday() not in self.config.target_weekdays:
            return False
        base = slot_start.replace(hour=0, minute=0, second=0, microsecond=0)
        targets = self._target_dates_for_day(base)
        return any(
            slot_start.hour == t.hour and slot_start.minute == t.minute
            for t in targets
        )

    def process_tenant(self, tenant_id: str, tenant_name: str, reservations_per_week: int = 1) -> None:
        """Check availability for one venue and book if a matching slot is found."""
        logger.info("Checking venue %s (%s)...", tenant_name or tenant_id, tenant_id)

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

        start_date = date.set_start_of_day(datetime.now())
        if week_matches >= reservations_per_week:
            start_date += timedelta(days=7 - start_date.weekday())
        else:
            start_date += timedelta(days=2)
        end_date = date.set_end_of_day(start_date)
        search_limit = datetime.now() + timedelta(days=14)

        while start_date < search_limit and not self.reservation_confirmed:
            try:
                entries = self.client.fetch_availability(tenant_id, start_date, end_date)
            except HTTPError as err:
                logger.warning("Availability fetch failed for %s: %s", start_date.date(), err)
                start_date += timedelta(days=1)
                end_date += timedelta(days=1)
                continue

            logger.info("Checking availability for %s...", start_date.strftime("%Y-%m-%d"))
            for entry in entries:
                self._process_availability_entry(entry, tenant_id)

            start_date += timedelta(days=1)
            end_date += timedelta(days=1)

    def _process_availability_entry(self, entry: Dict[str, Any], tenant_id: str) -> None:
        """Process one availability entry (one resource/date)."""
        resource_id = entry.get("resource_id")
        start_date_str = entry.get("start_date")
        slots = entry.get("slots") or []
        duration_minutes = int(self.config.duration_hours * 60)

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

            readable = slot_start.strftime("%Y %b %d - %H:%M")
            logger.info("Found matching slot: %s", readable)
            if not self.reservation_confirmed:
                self._reserve_court(tenant_id, resource_id, slot_start)

    def _reserve_court(self, tenant_id: str, resource_id: str, start_date: datetime) -> None:
        """Create payment intent, select payment method, confirm reservation."""
        duration_minutes = int(self.config.duration_hours * 60)
        data = self.client.prepare_payment_intent_data(
            tenant_id, resource_id, start_date, duration_minutes
        )
        try:
            payment_intent = self.client.create_payment_intent(data)
            methods = payment_intent.get("available_payment_methods") or []
            pay_at_club = next(
                (m for m in methods if m.get("name") == "Pay at the club"),
                None,
            )
            if not pay_at_club:
                pay_at_club = methods[0] if methods else None
            if not pay_at_club:
                logger.error("No payment method available")
                return
            self.client.update_payment_intent(
                payment_intent["payment_intent_id"],
                {
                    "selected_payment_method_id": pay_at_club.get("payment_method_id"),
                    "selected_payment_method_data": None,
                },
            )
            self.client.confirm_reservation(payment_intent["payment_intent_id"])
            logger.info("Reservation confirmed: %s", start_date.strftime("%Y %b %d - %H:%M"))
            self.reservation_confirmed = True
        except HTTPError as err:
            logger.exception(
                "Reservation failed: %s %s",
                getattr(err.response, "status_code", ""),
                getattr(err.response, "text", ""),
            )
