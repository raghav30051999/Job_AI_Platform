import os
import json
import base64
import threading
import time
import requests
import streamlit as st

REPO = os.getenv("GITHUB_REPO", "raghav30051999/Job_AI_Platform")  # must match your GitHub URL
BRANCH = "cloud-state"     # NON-deployed branch -> pushes never trigger redeploys
PATH = "db/jobs.json"


def _token():
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return os.getenv("GITHUB_TOKEN")


def fetch_jobs():
    """Read the live jobs.json from cloud-state (used once, at boot)."""
    tok = _token()
    if not tok:
        return None
    try:
        r = requests.get(
            f"https://api.github.com/repos/{REPO}/contents/{PATH}",
            params={"ref": BRANCH},
            headers={"Authorization": f"Bearer {tok}"},
            timeout=10,
        )
        if r.status_code == 200:
            return json.loads(base64.b64decode(r.json()["content"]))
    except Exception:
        pass
    return None


_state = {"dirty": False, "store": None}
_lock = threading.Lock()
_started = [False]


def push_jobs(store):
    """Mark store dirty; a background thread pushes it within ~5 seconds."""
    with _lock:
        _state["store"] = store
        _state["dirty"] = True
        if not _started[0]:
            _started[0] = True
            threading.Thread(target=_loop, daemon=True).start()


def _loop():
    while True:
        time.sleep(5)
        with _lock:
            if not _state["dirty"]:
                continue
            store = _state["store"]
            _state["dirty"] = False
        if not _do_push(store):
            with _lock:
                _state["dirty"] = True        # retry on next tick


def _do_push(store):
    tok = _token()
    if not tok:
        return True                            # local dev: nothing to do
    try:
        headers = {"Authorization": f"Bearer {tok}",
                   "Accept": "application/vnd.github+json"}
        url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
        sha = None
        g = requests.get(url, params={"ref": BRANCH}, headers=headers, timeout=10)
        if g.status_code == 200:
            sha = g.json().get("sha")
        body = {
            "message": "chore(cloud): persist job store",
            "content": base64.b64encode(json.dumps(store, indent=2).encode()).decode(),
            "branch": BRANCH,
        }
        if sha:
            body["sha"] = sha
        r = requests.put(url, headers=headers, json=body, timeout=20)
        return r.status_code in (200, 201)
    except Exception:
        return False