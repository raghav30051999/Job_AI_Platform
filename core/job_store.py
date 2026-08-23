import os
import json
import hashlib
from core.email_classifier import classify_email
from core import cloud_persist

DB_DIR = "db"
JOBS_PATH = os.path.join(DB_DIR, "jobs.json")
CLS_VERSION = 2

_cache = {"store": None}

def _load_local():
    if os.path.exists(JOBS_PATH):
        with open(JOBS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"next_id": 1, "jobs": {}, "deleted": []}

def _load():
    """Boot: hydrate from GitHub (cloud-state). After that, ALWAYS serve the
    in-session cache — refreshes/reruns can never revert to an old copy."""
    if _cache["store"] is not None:
        return _cache["store"]
    store = cloud_persist.fetch_jobs() or _load_local()
    _cache["store"] = store
    return store

def _save(store):
    os.makedirs(DB_DIR, exist_ok=True)
    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)
    _cache["store"] = store
    cloud_persist.push_jobs(store)   # lands on GitHub within ~5 seconds


def _make_job(store, mid, em, cls):
    job = {
        "id": f"JOB-{store['next_id']:03d}",
        "message_id": mid, "sig": em.get("sig", ""),
        "subject": em.get("subject", ""), "sender": em.get("sender", ""),
        "date": em.get("date", ""),
        "category": cls.get("category") if cls.get("category") in ("applied", "cold_offer") else "applied",
        "company_name": cls.get("company_name", "Unknown"),
        "job_role": cls.get("job_role", "Unknown"),
        "summary": cls.get("summary", ""),
        "mail_summary": cls.get("mail_summary", ""),
        "next_step": cls.get("next_step", ""),
        "notes": "", "edited": {}, "cls_v": CLS_VERSION,
    }
    store["next_id"] += 1
    return job


def sync_jobs(emails):
    store = _load()
    deleted = set(store.get("deleted", []))
    existing_sigs = {j.get("sig") for j in store["jobs"].values()}
    report = {"fetched": len(emails), "dup": 0, "not_job": 0, "added": 0,
              "retry": 0, "reclassified": 0}
    changed = False

    for em in emails:
        mid = em["message_id"]
        sig = hashlib.sha1(
            (em["subject"] + em["sender"] + em["body"]).encode("utf-8")
        ).hexdigest()

        if mid in store["jobs"] or sig in existing_sigs or mid in deleted or sig in deleted:
            report["dup"] += 1
            continue

        cls = classify_email(em["subject"], em["sender"], em["body"])

        if cls.get("is_job_related") is None:
            report["retry"] += 1      # API error -> don't save, retry next sync
            report["cls_err"] = cls.get("error", "")
            continue

        if not cls.get("is_job_related", False):
            report["not_job"] += 1
            store["jobs"][mid] = {
                "message_id": mid, "subject": em["subject"], "sender": em["sender"],
                "date": em["date"], "category": "not_job_related", "hidden": True,
                "sig": sig, "body": em["body"][:3000], "cls_v": CLS_VERSION,
            }
        else:
            report["added"] += 1
            em2 = dict(em)
            em2["sig"] = sig
            store["jobs"][mid] = _make_job(store, mid, em2, cls)

        existing_sigs.add(sig)
        changed = True

    # REPAIR PASS: re-evaluate hidden emails classified by an older classifier version
    for mid, j in list(store["jobs"].items()):
        if j.get("category") == "not_job_related" and j.get("cls_v", 1) != CLS_VERSION:
            cls = classify_email(j.get("subject", ""), j.get("sender", ""), j.get("body", ""))
            if cls.get("is_job_related") is None:
                continue                      # API failed -> leave untagged, retry next sync
            j["cls_v"] = CLS_VERSION
            if cls.get("is_job_related"):
                store["jobs"][mid] = _make_job(store, mid, j, cls)
                report["reclassified"] += 1
            changed = True

    if changed:
        _save(store)
    return store, report


def get_jobs():
    return _load()["jobs"]


def update_job(message_id, updates):
    store = _load()
    if message_id in store["jobs"]:
        store["jobs"][message_id].update(updates)
        _save(store)


def delete_by_ids(ids):
    store = _load()
    if "deleted" not in store:
        store["deleted"] = []
    remove = [mid for mid, j in store["jobs"].items() if j.get("id") in ids]
    for mid in remove:
        j = store["jobs"].pop(mid)
        store["deleted"].append(mid)
        if j.get("sig"):
            store["deleted"].append(j["sig"])
    _save(store)
    return len(remove)