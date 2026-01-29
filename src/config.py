"""Configuration loading from YAML and environment."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class TenantConfig(BaseModel):
    """One venue/club to book at."""
    id: str = Field(..., description="Playtomic tenant_id (venue ID)")
    name: str = Field("", description="Display name for logs")


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
    # When bookings open (for scheduling): optional, e.g. "08:00" if slots open at 8am
    booking_release_time: Optional[str] = Field(None, description="HH:MM when slots open (local)")


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
    """Get (email, password) from environment."""
    s = EnvSettings()
    email = os.environ.get("PLAYTOMIC_EMAIL") or s.playtomic_email
    password = os.environ.get("PLAYTOMIC_PASSWORD") or s.playtomic_password
    if not email or not password:
        raise ValueError(
            "Set PLAYTOMIC_EMAIL and PLAYTOMIC_PASSWORD in environment or .env"
        )
    return email, password
