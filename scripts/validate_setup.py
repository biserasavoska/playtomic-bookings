#!/usr/bin/env python3
"""
Validate config and Playtomic login without making a booking.
Run: python scripts/validate_setup.py
"""
import sys

# Add project root to path
sys.path.insert(0, ".")


def main() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    from src.config import load_booking_config, get_credentials
    from src.playtomic_client import PlaytomicClient

    print("1. Loading config...")
    config = load_booking_config()
    if not config.tenants:
        print("   ERROR: No tenants in config/booking_config.yaml. Add at least one venue (tenant id).")
        sys.exit(1)
    print(f"   OK: {len(config.tenants)} venue(s), hours {config.target_hours[:3]}..., weekdays {config.target_weekdays}")

    print("2. Reading credentials from env...")
    try:
        email, password = get_credentials()
        print(f"   OK: email set ({email[:3]}...)")
    except ValueError as e:
        print(f"   ERROR: {e}")
        sys.exit(1)

    print("3. Logging in to Playtomic...")
    try:
        client = PlaytomicClient(email, password)
        client.login()
        print("   OK: Login successful")
    except Exception as e:
        print(f"   ERROR: {e}")
        sys.exit(1)

    print("\nSetup looks good. Run 'python -m src.scheduler' to attempt a booking.")


if __name__ == "__main__":
    main()
