"""Configuration loading from YAML and environment."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

# Load .env into os.environ so get_credentials / get_credentials_for_account see PLAYTOMIC_EMAIL, PLAYTOMIC_EMAIL_2, etc.
load_dotenv()
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class TenantConfig(BaseModel):
    """One venue/club to book at."""
    id: str = Field(..., description="Playtomic tenant_id (venue ID)")
    name: str = Field("", description="Display name for logs")


class AccountConfig(BaseModel):
    """One Playtomic account with its own credentials and optional weekday/booking overrides."""
    env_email: str = Field(..., description="Env var name for email, e.g. PLAYTOMIC_EMAIL_TUESDAY")
    env_password: str = Field(..., description="Env var name for password, e.g. PLAYTOMIC_PASSWORD_TUESDAY")
    target_weekdays: List[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4],
        description="Weekdays this account books (0=Mon .. 6=Sun). E.g. [1] = Tuesday only.",
    )
    accept_any_time: Optional[bool] = Field(None, description="If true, this account accepts any time (overrides global)")
    booking_start_days_ahead: Optional[int] = Field(None, description="First day to search: 0=today, None=use global booking_days_ahead")
    booking_days_ahead: Optional[int] = Field(None, description="Search window in days (e.g. 14 = today..today+14 when start is 0)")


class BookingConfig(BaseModel):
    """Booking preferences from config file."""
    # Target time slots as HH:MM (e.g. 18:00, 18:30, ..., 21:30)
    target_hours: List[str] = Field(
        default_factory=lambda: ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"],
        description="Preferred start times",
    )
    # Weekdays only: 0=Mon, 4=Fri
    weekdays_only: bool = True
    target_weekdays: List[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4],
        description="0=Monday .. 6=Sunday",
    )
    duration_hours: float = Field(1.5, ge=1.0, le=2.0, description="Slot duration in hours")
    reservations_per_week: int = Field(1, ge=1, description="Max reservations per week")
    tenants: List[TenantConfig] = Field(default_factory=list, description="Venues to try")
    # Try these times first (e.g. ["19:00"]). If empty, all target_hours are equal.
    preferred_hours: List[str] = Field(default_factory=list, description="Preferred start times (tried first)")
    # If true, accept any slot on target weekdays (not only target_hours). Useful for testing.
    accept_any_time: bool = Field(False, description="Book any time on target days (ignores target_hours)")
    # How many days ahead slots open (e.g. 14 = book the day that opens 14 days from today at 8:30)
    booking_days_ahead: int = Field(14, ge=1, le=30, description="Days ahead when club opens slots")
    # First day to search (None = use booking_days_ahead as first day; 0 = search from today). Per-account override in accounts.
    booking_start_days_ahead: Optional[int] = Field(None, description="0=search from today; None=start at booking_days_ahead")
    # When bookings open (for scheduling): optional, e.g. "08:30" if slots open at 8:30
    booking_release_time: Optional[str] = Field(None, description="HH:MM when slots open (local or use timezone below)")
    # Timezone for release time (e.g. Europe/Brussels for CET). Required on GitHub Actions (runner is UTC).
    booking_release_timezone: Optional[str] = Field(None, description="IANA timezone for booking_release_time, e.g. Europe/Brussels")
    # Multiple accounts: each books on its target_weekdays. If empty, use single PLAYTOMIC_EMAIL/PASSWORD.
    accounts: List[AccountConfig] = Field(default_factory=list, description="Multiple accounts with per-account weekdays")


def load_booking_config(path: Optional[Path] = None) -> BookingConfig:
    """Load booking_config.yaml and return validated BookingConfig."""
    from .utils.directory import get_config_path
    config_path = path or get_config_path()
    if not config_path.exists():
        return BookingConfig()
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    return BookingConfig(**data)


class EnvSettings(BaseSettings):
    """Credentials and paths from environment (never commit)."""
    playtomic_email: str = Field("", alias="PLAYTOMIC_EMAIL")
    playtomic_password: str = Field("", alias="PLAYTOMIC_PASSWORD")
    config_path: Optional[str] = Field(None, alias="PLAYTOMIC_CONFIG_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_credentials() -> Tuple[str, str]:
    """Get (email, password) from environment (PLAYTOMIC_EMAIL, PLAYTOMIC_PASSWORD)."""
    s = EnvSettings()
    email = os.environ.get("PLAYTOMIC_EMAIL") or s.playtomic_email
    password = os.environ.get("PLAYTOMIC_PASSWORD") or s.playtomic_password
    if not email or not password:
        raise ValueError(
            "Set PLAYTOMIC_EMAIL and PLAYTOMIC_PASSWORD in environment or .env"
        )
    return email, password


def get_credentials_for_account(env_email_key: str, env_password_key: str) -> Tuple[str, str]:
    """Get (email, password) from environment using given env var names."""
    email = os.environ.get(env_email_key) or ""
    password = os.environ.get(env_password_key) or ""
    if not email or not password:
        raise ValueError(
            f"Set {env_email_key} and {env_password_key} in environment or .env"
        )
    return email, password
