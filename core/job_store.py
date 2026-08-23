import os
import json
import hashlib
from core.email_classifier import classify_email
from core.dedup import is_hard_duplicate

DB_DIR = "db"
JOBS_PATH = os.path.join(DB_DIR, "jobs.json")


def _load():
    if os.path.exists(JOBS_PATH):
        with open(JOBS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"next_id": 1, "jobs": {}, "deleted": []}


def _save(store):
    os.makedirs(DB_DIR, exist_ok=True)
    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def sync_jobs(emails):
    store = _load()
    deleted = set(store.get("deleted", []))
    existing_sigs = {j.get("sig") for j in store["jobs"].values()}
    report = {"fetched": len(emails), "dup": 0, "not_job": 0, "added": 0}
    changed = False
    for em in emails:
        mid = em["message_id"]
        sig = hashlib.sha1(
            (em["subject"] + em["sender"] + em["body"]).encode("utf-8")
        ).hexdigest()

        # skip: already stored, duplicate content, or previously deleted
        if mid in store["jobs"] or sig in existing_sigs or mid in deleted or sig in deleted:
            report["dup"] += 1
            continue

        cls = classify_email(em["subject"], em["sender"], em["body"])

        if not cls.get("is_job_related", False):
            report["not_job"] += 1
            store["jobs"][mid] = {
                "message_id": mid, "subject": em["subject"], "sender": em["sender"],
                "date": em["date"], "category": "not_job_related", "hidden": True,
                "sig": sig,
            }
        else:
            report["added"] += 1
            store["jobs"][mid] = {
                "id": f"JOB-{store['next_id']:03d}",
                "message_id": mid, "sig": sig,
                "subject": em["subject"], "sender": em["sender"], "date": em["date"],
                "category": cls.get("category", "applied"),
                "company_name": cls.get("company_name", "Unknown"),
                "job_role": cls.get("job_role", "Unknown"),
                "summary": cls.get("summary", ""),
                "mail_summary": cls.get("mail_summary", ""),
                "next_step": cls.get("next_step", ""),
                "notes": "", "edited": {},
            }
            store["next_id"] += 1

        existing_sigs.add(sig)
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