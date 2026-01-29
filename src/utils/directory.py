"""Directory and config path utilities."""
import os
from pathlib import Path


def get_config_dir() -> Path:
    """Get config directory (project config/ or env PLAYTOMIC_CONFIG_DIR)."""
    env_path = os.environ.get("PLAYTOMIC_CONFIG_DIR")
    if env_path and os.path.exists(env_path):
        return Path(env_path)
    # Default: project root / config
    project_root = Path(__file__).resolve().parent.parent.parent
    default = project_root / "config"
    default.mkdir(parents=True, exist_ok=True)
    return default


def get_config_path() -> Path:
    """Path to booking_config.yaml."""
    return get_config_dir() / "booking_config.yaml"
