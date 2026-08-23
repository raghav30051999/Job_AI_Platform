import os
import json
import base64
import threading
import time
import requests
import streamlit as st

REPO = os.getenv("GITHUB_REPO", "raghav30051999/job_ai_platform")
BRANCH = "cloud-state"
PATH = "db/jobs.json"


def _token():
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return os.getenv("GITHUB_TOKEN")


def fetch_jobs():
    """Read live jobs.json from the cloud-state branch. None if unavailable."""
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


# ---------- reliable background pusher (never loses the final state) ----------
_state = {"dirty": False, "store": None}
_lock = threading.Lock()
_started = [False]


def push_jobs(store):
    """Mark store for background push; a single daemon thread pushes the
    latest state every ~20s. Non-blocking, conflict-safe, retry-safe."""
    with _lock:
        _state["store"] = store
        _state["dirty"] = True
        if not _started[0]:
            _started[0] = True
            threading.Thread(target=_loop, daemon=True).start()


def _loop():
    while True:
        time.sleep(20)
        with _lock:
            if not _state["dirty"]:
                continue
            store = _state["store"]
            _state["dirty"] = False
        if not _do_push(store):
            with _lock:
                _state["dirty"] = True      # retry next tick


def _do_push(store):
    tok = _token()
    if not tok:
        return True                          # nothing to do locally
    try:
        headers = {"Authorization": f"Bearer {tok}",
                   "Accept": "application/vnd.github+json"}
        url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
        sha = None
        g = requests.get(url, params={"ref": BRANCH}, headers=headers, timeout=10)
        if g.status_code == 200:
            sha = g.json().get("sha")
        body = {
            "message": "chore(cloud): persist synced job store",
            "content": base64.b64encode(json.dumps(store, indent=2).encode()).decode(),
            "branch": BRANCH,
        }
        if sha:
            body["sha"] = sha
        r = requests.put(url, headers=headers, json=body, timeout=20)
        return r.status_code in (200, 201)
    except Exception:
        return False