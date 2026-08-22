import os
import json
import hashlib
import datetime
from core.job_store import get_jobs
from core.gemini_client import generate_json
from core.profile_rag import fit_score, search_profile

RECO_PATH = os.path.join("db", "reco.json")

SYSTEM = ("You are an expert career coach. Always return valid JSON only. "
          "No extra commentary.")


def _visible_jobs():
    out = []
    for mid, j in get_jobs().items():
        d = {**j, **j.get("edited", {})}
        if d.get("category") in ("applied", "cold_offer"):
            out.append((mid, d))
    return out


def _job_text(d):
    return (f"{d.get('job_role', '')} {d.get('company_name', '')} "
            f"{d.get('summary', '')} {d.get('mail_summary', '')}")


def _sig(pairs, personal):
    blob = ("P|" if personal else "G|") + "|".join(sorted(
        f"{d['id']}:{d.get('date', '')}:{d.get('category', '')}:{d.get('company_name', '')}"
        for _, d in pairs
    ))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def _fallback(pairs, personal):
    def key(item):
        _, d = item
        try:
            dt = datetime.datetime.strptime(d["date"][:10], "%Y-%m-%d")
        except Exception:
            dt = datetime.datetime.min
        fit = (fit_score(_job_text(d)) or 0) / 100.0 if personal else 0.0
        return (fit, 0.5 if d.get("category") == "applied" else 0, dt)

    top = sorted(pairs, key=key, reverse=True)[:3]
    picks = []
    for i, (_, d) in enumerate(top):
        fit = fit_score(_job_text(d)) if personal else None
        reason = d.get("next_step", "Review this opportunity and respond promptly.")
        if fit is not None:
            reason = f"{fit}% profile match — {reason}"
        picks.append({
            "id": d["id"],
            "company": d.get("company_name", "Unknown"),
            "role": d.get("job_role", "Unknown"),
            "priority": ["High", "Medium", "Low"][min(i, 2)],
            "reason": reason,
            "match": fit,
        })
    return {
        "picks": picks,
        "keywords": [],
        "strategy": ("Ranked by profile fit & recency (offline mode)." if personal
                     else "Ranked by urgency & recency (offline mode).")
                    + " Press Refresh once Gemini is reachable.",
        "source": "fallback",
    }


def _llm_reco(pairs, personal):
    listing = []
    for _, d in pairs:
        item = {
            "id": d["id"],
            "category": d.get("category"),
            "company": d.get("company_name", "Unknown"),
            "role": d.get("job_role", "Unknown"),
            "date": d.get("date", ""),
            "mail_summary": d.get("mail_summary", ""),
            "next_step": d.get("next_step", ""),
        }
        if personal:
            jt = _job_text(d)
            item["fit_score"] = fit_score(jt)
            item["profile_highlights"] = [c["text"][:300] for _, c in search_profile(jt, 2)]
        listing.append(item)

    prompt = (
        "Below is the candidate's current job pipeline.\n"
        "Rank the BEST opportunities to focus on RIGHT NOW (max 3), weighing:\n"
        "- urgency (interview invites / time-bound actions beat generic outreach)\n"
        "- recency\n"
        "- clarity of the role\n"
    )
    if personal:
        prompt += (
            "- fit_score (0-100 similarity to the candidate's profile) and profile_highlights\n"
            "Start each reason with the match percentage, e.g. '78% match - ...'.\n"
        )
    prompt += (
        "\nAlso extract 5-8 resume keywords/skills that appear across these opportunities, "
        "and give ONE short strategy sentence for this week.\n\n"
        f"PIPELINE JSON:\n{json.dumps(listing, indent=1)}\n\n"
        "Return JSON exactly in this shape:\n"
        '{"picks":[{"id":string,"company":string,"role":string,'
        '"priority":"High|Medium|Low","reason":string,"match":number|null}],'
        '"keywords":[string],"strategy":string}'
    )
    data = generate_json(prompt, system_instruction=SYSTEM)
    return {
        "picks": [p for p in data.get("picks", []) if p.get("id")][:3],
        "keywords": [str(k) for k in data.get("keywords", [])][:8],
        "strategy": data.get("strategy", ""),
        "source": "gemini",
    }


def get_recommendations(force=False, personal=False):
    pairs = _visible_jobs()
    if not pairs:
        return None

    sig = _sig(pairs, personal)
    if not force and os.path.exists(RECO_PATH):
        try:
            with open(RECO_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("sig") == sig:
                return cached["payload"]
        except Exception:
            pass

    try:
        payload = _llm_reco(pairs, personal)
    except Exception:
        payload = _fallback(pairs, personal)

    payload["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    payload["mode"] = "personalized" if personal else "generic"
    os.makedirs("db", exist_ok=True)
    with open(RECO_PATH, "w", encoding="utf-8") as f:
        json.dump({"sig": sig, "payload": payload}, f, indent=2)
    return payload