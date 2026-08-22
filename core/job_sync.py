import time
from core.email_reader import fetch_recent_emails
from core.job_store import sync_jobs, get_jobs
from core.settings import get_scan_since

STATUS = {
    "last_ok": None,
    "last_err": None,
    "report": None,
    "running": False,
}

_lock = {
    "running": False,
    "last_attempt": 0.0,
}


def _normalize_report(report):
    """
    Some report dictionaries may contain keys with accidental spaces.
    Example: "added " instead of "added".
    This normalizes keys safely.
    """
    if not isinstance(report, dict):
        return {
            "fetched": 0,
            "dup": 0,
            "not_job": 0,
            "added": 0,
        }

    return {str(k).strip(): v for k, v in report.items()}


def sync_now(force=True, limit=50):
    """
    Sync recent emails and create job entries.

    force=True bypasses the short cooldown, useful for the Sync Now button.
    """
    now = time.time()

    # Prevent concurrent syncs
    if _lock["running"]:
        return

    # Prevent accidental rapid repeated syncs unless forced
    if not force and now - _lock["last_attempt"] < 2:
        return

    _lock["running"] = True
    _lock["last_attempt"] = now
    STATUS["running"] = True

    try:
        since = get_scan_since()

        # Pass since directly so fetch_recent_emails can filter earlier
        emails = fetch_recent_emails(limit=limit, since=since)

        # Safety filter in case fetch_recent_emails does not fully filter
        emails = [
            e for e in emails
            if e.get("_dt") is None or e.get("_dt") >= since
        ]

        # Count visible jobs before sync
        before_visible = {
            mid for mid, job in get_jobs().items()
            if not job.get("hidden")
        }

        result = sync_jobs(emails)

        # sync_jobs currently returns: store, report
        if isinstance(result, tuple) and len(result) == 2:
            _, report = result
        else:
            report = {
                "fetched": len(emails),
                "dup": 0,
                "not_job": 0,
                "added": 0,
            }

        report = _normalize_report(report)

        report.setdefault("fetched", len(emails))
        report.setdefault("dup", 0)
        report.setdefault("not_job", 0)
        report.setdefault("added", 0)

        # If report.added is missing or zero, calculate visible added jobs
        after_visible = {
            mid for mid, job in get_jobs().items()
            if not job.get("hidden")
        }

        if not report.get("added"):
            report["added"] = len(after_visible - before_visible)

        STATUS["report"] = report
        STATUS["last_ok"] = time.strftime("%H:%M:%S")
        STATUS["last_err"] = None

    except Exception as e:
        STATUS["last_err"] = str(e)

    finally:
        _lock["running"] = False
        STATUS["running"] = False 