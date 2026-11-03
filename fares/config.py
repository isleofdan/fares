"""Paths and route profiles."""

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Persistent place for the store, page and logs; outside the repository so it survives
# a fresh clone and a machine deploy. FARES_DATA overrides it (tests use a temp folder).
DATA_DIR = Path(os.environ.get("FARES_DATA", "/data/home/dan/fares-data"))


def store_path() -> Path:
    return DATA_DIR / "fares.sqlite"


def capture_log_path() -> Path:
    return DATA_DIR / "capture.log"


def page_path() -> Path:
    return DATA_DIR / "fares.html"


def load_profiles() -> dict:
    with open(REPO / "routes.json", encoding="utf-8") as f:
        return json.load(f)
