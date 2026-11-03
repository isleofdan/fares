"""Paths and route profiles."""

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Persistent place for the store, page and logs; outside the repository so it survives
# a fresh clone and a machine deploy. FARES_DATA overrides it (tests use a temp folder).
DATA_DIR = Path(os.environ.get("FARES_DATA", "/data/home/dan/fares-data"))


# The Spine's fares route on its private listener (isleofdan/spine README.md, "The private
# listener": from another app in Dan's Fly organization, http://spine-dan.internal:8080). No token:
# the listener takes plain http from Dan's Fly private network. FARES_SPINE_URL overrides it;
# bin/page --spine overrides both.
SPINE_URL = "http://spine-dan.internal:8080/internal/fares/page"


def spine_url() -> str:
    return os.environ.get("FARES_SPINE_URL") or SPINE_URL


def store_path() -> Path:
    return DATA_DIR / "fares.sqlite"


def capture_log_path() -> Path:
    return DATA_DIR / "capture.log"


def page_path() -> Path:
    return DATA_DIR / "fares.html"


def load_profiles() -> dict:
    with open(REPO / "routes.json", encoding="utf-8") as f:
        return json.load(f)
