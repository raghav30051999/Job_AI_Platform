import re

_SUFFIX = (r"\b(inc|incorporated|llc|ltd|limited|pvt|private|corp|corporation|co|company|"
           r"technologies|technology|tech|solutions|services|labs|india|llp)\b")

def norm_company(name):
    s = re.sub(r"\(.*?\)", " ", (name or "").lower())
    s = re.sub(_SUFFIX, " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def norm_role(title):
    s = re.sub(r"\(.*?\)", " ", (title or "").lower())
    s = re.sub(r"[^a-z0-9+#]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def sig_of(job):
    return (norm_company(job.get("company_name")), norm_role(job.get("job_role")))

def collapse_duplicates(jobs, threshold=2):
    """
    Groups jobs by (normalized company, normalized role).
    If group size > threshold, keeps only the newest and adds a dup_count badge.
    """
    shown, groups = [], {}
    
    for j in jobs:
        key = sig_of(j)
        # Never group if company is missing or "Unknown"
        if not key[0] or key[0] == "unknown":
            shown.append(j)
            continue
            
        groups.setdefault(key, []).append(j)

    for grp in groups.values():
        # Sort by date descending to keep the newest
        grp.sort(key=lambda x: x.get("date", ""), reverse=True)
        if len(grp) > threshold:
            top = dict(grp[0])
            top["dup_count"] = len(grp)
            shown.append(top)
        else:
            shown.extend(grp)

    shown.sort(key=lambda x: x.get("date", ""), reverse=True)
    return shown