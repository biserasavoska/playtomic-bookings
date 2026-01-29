"""
Playtomic API client (reverse-engineered from app behavior).
Uses same endpoints as the official app: auth at v3, booking/availability at v1.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Text

import pytz
import requests

logger = logging.getLogger(__name__)

# Web app (session/cookie auth); login and availability use playtomic.com
WEB_BASE = "https://playtomic.com"
WEB_LOGIN_URL = f"{WEB_BASE}/api/web-app/login"
WEB_AVAILABILITY_URL = f"{WEB_BASE}/api/clubs/availability"
# Payment: "Continue" opens app.playtomic.com/payments?type=CUSTOMER_MATCH&...
APP_BASE = "https://app.playtomic.com"
PAYMENT_API_URL = f"{APP_BASE}/api/v1"
# playtomic.io API (playtomic-scheduler style): token auth, may work for payment_intents
IO_BASE = "https://playtomic.io"
IO_AUTH_URL = f"{IO_BASE}/api/v3/auth/login"
IO_API_URL = f"{IO_BASE}/api/v1"
# api.playtomic.io: alternative payment API; web login token may work here when playtomic.io login fails
API_IO_BASE = "https://api.playtomic.io"
API_IO_V1 = f"{API_IO_BASE}/v1"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        # playtomic.io token (for payment API when .com returns HTML)
        self.playtomic_io_token: Optional[str] = None
        self.playtomic_io_user_id: Optional[str] = None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": USER_AGENT,
            "X-Requested-With": "com.playtomic.web",
            "Origin": "https://playtomic.com",
            "Referer": "https://playtomic.com/",
            "Content-Type": "application/json",
        }

    def login(self) -> Dict[str, Any]:
        """Login via web-app endpoint; may set session cookies or return token."""
        url = WEB_LOGIN_URL
        data = {"email": self.email, "password": self.password}
        response = self.session.post(
            url,
            json=data,
            timeout=15,
            allow_redirects=True,
        )
        response.raise_for_status()
        # Try JSON body (token-style API)
        try:
            body = response.json()
            self.access_token = body.get("access_token") or body.get("token")
            self.user_id = body.get("user_id") or (str(body.get("user_id")) if body.get("user_id") is not None else None)
            if self.access_token and self.access_token != "__session__":
                self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            return body
        except Exception:
            pass
        # Session/cookie auth: no token in body; session cookies are in self.session
        self.access_token = "__session__"
        self.user_id = None
        return {}

    def ensure_logged_in(self) -> None:
        if not self.access_token:
            self.login()

    def login_playtomic_io(self) -> bool:
        """Login at playtomic.io to get Bearer token for payment API. Returns True if token obtained."""
        try:
            resp = self.session.post(
                IO_AUTH_URL,
                json={"email": self.email, "password": self.password},
                timeout=15,
                allow_redirects=False,
            )
            resp.raise_for_status()
            body = resp.json()
            token = body.get("access_token") or body.get("token")
            uid = body.get("user_id")
            if uid is not None:
                uid = str(uid)
            if token and token != "__session__":
                self.playtomic_io_token = token
                self.playtomic_io_user_id = uid
                logger.info("playtomic.io login OK (token for payment API)")
                return True
        except Exception as e:
            logger.warning(
                "playtomic.io login failed (will try api.playtomic.io with web token, then app.playtomic.com): %s",
                e,
            )
        self.playtomic_io_token = None
        self.playtomic_io_user_id = None
        return False

    def fetch_availability(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch availability for a tenant; uses playtomic.com per-day API (session auth)."""
        self.ensure_logged_in()
        # playtomic.com uses single date param per request; loop day by day
        from datetime import timedelta
        results: List[Dict[str, Any]] = []
        day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_day = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        while day <= end_day:
            params = {
                "tenant_id": tenant_id,
                "date": day.strftime("%Y-%m-%d"),
                "sport_id": "PADEL",
            }
            response = self.session.get(WEB_AVAILABILITY_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                results.extend(data)
            day += timedelta(days=1)
        return results if results else []

    def _payment_headers(self) -> Dict[str, str]:
        """Headers for app.playtomic.com payment API (same domain as payments page)."""
        return {"Origin": APP_BASE, "Referer": f"{APP_BASE}/"}

    def _use_playtomic_io_payment(self) -> bool:
        """True if we have playtomic.io Bearer token for payment."""
        return bool(self.playtomic_io_token)

    def _use_web_token_payment(self) -> bool:
        """True if we should try api.playtomic.io with web login token (when playtomic.io login failed)."""
        if self.playtomic_io_token:
            return False
        return bool(self.access_token and self.access_token != "__session__")

    def _payment_request_headers(self) -> Dict[str, str]:
        """Headers for payment API: playtomic.io or api.playtomic.io use Bearer; app.playtomic.com uses session."""
        if self._use_playtomic_io_payment():
            return {
                "Authorization": f"Bearer {self.playtomic_io_token}",
                "Origin": IO_BASE,
                "Referer": f"{IO_BASE}/",
                "Content-Type": "application/json",
            }
        if self._use_web_token_payment():
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Origin": API_IO_BASE,
                "Referer": f"{API_IO_BASE}/",
                "Content-Type": "application/json",
            }
        return self._payment_headers()

    def _payment_base_url(self) -> str:
        """Base URL for payment_intents: playtomic.io > api.playtomic.io (web token) > app.playtomic.com."""
        if self._use_playtomic_io_payment():
            return IO_API_URL
        if self._use_web_token_payment():
            return API_IO_V1
        return PAYMENT_API_URL

    def create_payment_intent(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment intent (playtomic.io > api.playtomic.io with web token > app.playtomic.com)."""
        self.ensure_logged_in()
        base = self._payment_base_url()
        if base == API_IO_V1:
            logger.info("Using api.playtomic.io for payment (web login token)")
        payload = dict(data)
        if self._use_playtomic_io_payment() and self.playtomic_io_user_id:
            payload["user_id"] = self.playtomic_io_user_id
        if base == PAYMENT_API_URL:
            # Warm up app.playtomic.com session
            cart = payload.get("cart", {}) or {}
            item = cart.get("requested_item", {}) or {}
            item_data = item.get("cart_item_data", {}) or {}
            if item_data:
                start = item_data.get("start", "")
                duration_hours = item_data.get("duration", 1.5)
                duration_mins = int(round(duration_hours * 60))
                params = {
                    "type": "CUSTOMER_MATCH",
                    "tenant_id": item_data.get("tenant_id", ""),
                    "resource_id": item_data.get("resource_id", ""),
                    "start": start,
                    "duration": duration_mins,
                }
                try:
                    self.session.get(
                        f"{APP_BASE}/payments",
                        params=params,
                        headers=self._payment_headers(),
                        timeout=10,
                    )
                except Exception:
                    pass
        response = self.session.post(
            f"{base}/payment_intents",
            json=payload,
            headers=self._payment_request_headers(),
            timeout=10,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            body_preview = (response.text or "")[:500]
            used = "playtomic.io" if self._use_playtomic_io_payment() else (
                "api.playtomic.io (web token)" if self._use_web_token_payment() else "app.playtomic.com"
            )
            logger.error(
                "Payment API returned HTML instead of JSON (url=%s, tried %s). "
                "The server sent the web app page instead of a booking response. See PAYMENT_API_TROUBLESHOOTING.md.",
                response.url,
                used,
            )
            logger.debug("Response body start: %r", body_preview)
            raise ValueError(
                "Payment API returned HTML instead of JSON. "
                "playtomic.io login may have failed and app.playtomic.com returns the web app page. "
                "See PAYMENT_API_TROUBLESHOOTING.md to capture the real booking request from your browser."
            ) from None

    def update_payment_intent(self, payment_intent_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update payment intent (e.g. select payment method)."""
        self.ensure_logged_in()
        base = self._payment_base_url()
        response = self.session.patch(
            f"{base}/payment_intents/{payment_intent_id}",
            json=data,
            headers=self._payment_request_headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def confirm_reservation(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm the reservation."""
        self.ensure_logged_in()
        base = self._payment_base_url()
        response = self.session.post(
            f"{base}/payment_intents/{payment_intent_id}/confirmation",
            headers=self._payment_request_headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def get_matches(self, size: int = 10, sort: str = "start_date,desc") -> List[Dict[str, Any]]:
        """Get list of matches; returns [] when using session auth (api.playtomic.io 404)."""
        self.ensure_logged_in()
        if self.access_token == "__session__":
            return []  # matches endpoint not available with web session
        url = f"{PAYMENT_API_URL}/matches"
        params = {"size": str(size), "sort": sort, "owner_id": self.user_id or "me"}
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

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
