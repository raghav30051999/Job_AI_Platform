import os
import json
from datetime import datetime

SETTINGS_PATH = os.path.join("db", "settings.json")


def _load():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    return {}


def _save(s):
    os.makedirs("db", exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(s, f, indent=2)


def get_scan_since():
    """First call = today (baseline). Later calls return the same baseline."""
    s = _load()
    if "scan_since" not in s:
        s["scan_since"] = datetime.now().isoformat()
        _save(s)
    return datetime.fromisoformat(s["scan_since"])