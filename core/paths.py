"""
Central path resolver for Hidayat AI (Ultron Jarvis).

Works in normal script mode AND frozen exe mode (PyInstaller / Nuitka).
No third-party dependencies — stdlib only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Frozen detection
# ---------------------------------------------------------------------------

def is_frozen() -> bool:
    """Return True when running inside a PyInstaller / Nuitka bundle."""
    return getattr(sys, "frozen", False)


# ---------------------------------------------------------------------------
# Base directory
# ---------------------------------------------------------------------------

def get_base_dir() -> Path:
    """Return the root directory of the application.

    Frozen mode: the directory containing the executable.
    Normal mode: the directory two levels up from *this* file (project root).
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Data directory (with settings-file override)
# ---------------------------------------------------------------------------

_APP_SETTINGS_FILENAME = "app_settings.json"


def _read_app_settings() -> dict:
    """Best-effort read of ``config/app_settings.json``.

    Returns an empty dict on any failure (file missing, bad JSON, etc.).
    """
    settings_path = get_base_dir() / "config" / _APP_SETTINGS_FILENAME
    try:
        return json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def get_data_dir() -> Path:
    """Return the root data directory.

    Resolution order:
      1. ``data_directory`` in *app_settings.json* (if non-empty).
      2. Portable mode — ``use_portable_mode`` true → ``<base>/data``.
      3. ``%APPDATA%/UltronJarvis`` on Windows (``~/.UltronJarvis`` elsewhere).
      4. ``<base>/data`` fallback.
    """
    settings = _read_app_settings()

    # 1. Explicit override from settings
    explicit = settings.get("data_directory", "")
    if explicit:
        return Path(explicit).expanduser().resolve()

    # 2. Portable mode
    if settings.get("use_portable_mode", False):
        return get_base_dir() / "data"

    # 3. OS-standard user data location
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "UltronJarvis"
    else:
        home = Path.home()
        if home:
            return home / ".UltronJarvis"

    # 4. Fallback — bundle next to the source / executable
    return get_base_dir() / "data"


# ---------------------------------------------------------------------------
# Sub-directories
# ---------------------------------------------------------------------------

def get_config_dir() -> Path:
    """Return ``<data_dir>/config``."""
    return get_data_dir() / "config"


def get_memory_dir() -> Path:
    """Return ``<data_dir>/memory``."""
    return get_data_dir() / "memory"


def get_backups_dir() -> Path:
    """Return ``<data_dir>/backups``."""
    return get_data_dir() / "backups"


def get_uploads_dir() -> Path:
    """Return ``<data_dir>/uploads``."""
    return get_data_dir() / "uploads"


# ---------------------------------------------------------------------------
# Directory bootstrapping
# ---------------------------------------------------------------------------

def ensure_data_dirs() -> Path:
    """Create every required sub-directory and return ``get_data_dir()``."""
    for subdir in (get_config_dir, get_memory_dir, get_backups_dir, get_uploads_dir):
        subdir().mkdir(parents=True, exist_ok=True)
    return get_data_dir()
