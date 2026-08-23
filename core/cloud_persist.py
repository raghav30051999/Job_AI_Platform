import os
import json
import base64
import threading
import time
import requests
import streamlit as st

REPO = os.getenv("GITHUB_REPO", "raghav30051999/job_ai_platform")  # adjust if different
BRANCH = "cloud-state"
PATH = "db/jobs.json"


def _token():
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return os.getenv("GITHUB_TOKEN")


def fetch_jobs():
    """Read the live jobs.json from the cloud-state branch. None if unavailable."""
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


_last_push = [0.0]

def push_jobs(store, debounce=20):
    """Background-push jobs.json to cloud-state (debounced). No-op without token."""
    tok = _token()
    if not tok:
        return
    now = time.time()
    if now - _last_push[0] < debounce:
        return
    _last_push[0] = now

    def _do():
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
            requests.put(url, headers=headers, json=body, timeout=20)
        except Exception:
            pass  # never let persistence break the app

    threading.Thread(target=_do, daemon=True).start()