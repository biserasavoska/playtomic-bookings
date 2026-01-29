"""
Playtomic API client (reverse-engineered from app behavior).
Uses same endpoints as the official app: auth at v3, booking/availability at v1.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Text

import pytz
import requests

API_URL = "https://playtomic.io/api/v1"
AUTH_URL = "https://playtomic.io/api/v3"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
)


class PlaytomicClient:
    """Client for Playtomic API: login, availability, payment intents, confirm reservation."""

    def __init__(self, email: str, password: str) -> None:
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": USER_AGENT,
            "X-Requested-With": "com.playtomic.web",
        }

    def login(self) -> Dict[str, Any]:
        """Login to Playtomic; sets access_token and user_id."""
        url = f"{AUTH_URL}/auth/login"
        data = {"email": self.email, "password": self.password}
        response = self.session.post(url, json=data, timeout=10)
        response.raise_for_status()
        body = response.json()
        self.access_token = body.get("access_token")
        self.user_id = body.get("user_id")
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        return body

    def ensure_logged_in(self) -> None:
        if not self.access_token:
            self.login()

    def fetch_availability(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch availability for a tenant (venue) between start_date and end_date."""
        self.ensure_logged_in()
        url = f"{API_URL}/availability"
        params = {
            "user_id": "me",
            "tenant_id": tenant_id,
            "sport_id": "PADEL",
            "local_start_min": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "local_start_max": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def create_payment_intent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment intent for a court booking."""
        self.ensure_logged_in()
        response = self.session.post(f"{API_URL}/payment_intents", json=data, timeout=10)
        response.raise_for_status()
        return response.json()

    def update_payment_intent(self, payment_intent_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update payment intent (e.g. select payment method)."""
        self.ensure_logged_in()
        response = self.session.patch(
            f"{API_URL}/payment_intents/{payment_intent_id}", json=data, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def confirm_reservation(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm the reservation."""
        self.ensure_logged_in()
        response = self.session.post(
            f"{API_URL}/payment_intents/{payment_intent_id}/confirmation", timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_matches(self, size: int = 10, sort: str = "start_date,desc") -> List[Dict[str, Any]]:
        """Get list of matches for the current user."""
        self.ensure_logged_in()
        url = f"{API_URL}/matches"
        params = {"size": str(size), "sort": sort, "owner_id": self.user_id}
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def prepare_payment_intent_data(
        self,
        tenant_id: str,
        resource_id: str,
        start_date: datetime,
        duration_minutes: int,
    ) -> Dict[str, Any]:
        """Build payload for create_payment_intent (court booking)."""
        utc_start = start_date.astimezone(pytz.utc)
        duration_hours = duration_minutes / 60.0
        return {
            "allowed_payment_method_types": [
                "OFFER", "CASH", "MERCHANT_WALLET", "DIRECT",
                "SWISH", "IDEAL", "BANCONTACT", "PAYTRAIL",
                "CREDIT_CARD", "QUICK_PAY",
            ],
            "user_id": self.user_id,
            "cart": {
                "requested_item": {
                    "cart_item_type": "CUSTOMER_MATCH",
                    "cart_item_voucher_id": None,
                    "cart_item_data": {
                        "supports_split_payment": True,
                        "number_of_players": 4,
                        "tenant_id": tenant_id,
                        "resource_id": resource_id,
                        "start": utc_start.strftime("%Y-%m-%dT%H:%M:%S"),
                        "duration": duration_hours,
                        "match_registrations": [{"user_id": self.user_id, "pay_now": True}],
                    },
                }
            },
        }
