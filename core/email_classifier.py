import time
from core.gemini_client import generate_json

SYSTEM = """You are an expert email classifier for a job-seeking assistant.
Always return valid JSON only. No extra commentary.

JOB-RELATED includes: job postings; application confirmations; resume shortlist notices;
interview invitations/reschedules; assessments; offer letters; rejections; recruiter outreach.

NOT JOB-RELATED: newsletters, marketing, spam, generic account notices.

Return JSON:
{"is_job_related": bool,
 "category": "applied" | "cold_offer",
 "company_name": str, "job_role": str,
 "summary": str, "mail_summary": str, "next_step": str}

category = "applied" when the email responds to the candidate's application
(shortlist, interview, offer, rejection, assessment) or is a job posting;
"cold_offer" when a recruiter contacted the candidate unprompted.

company_name: from signature/sender (e.g., "Salesforce India").
job_role: from subject/body (e.g., "Data Analyst").
next_step: actionable (e.g., "Attend virtual interview on 28 Aug 2026 at 1:00 PM IST").
When in doubt, prefer true for anything mentioning roles, resumes, or interviews."""


def classify_email(subject, sender, body, attempts=3):
    """Classify with automatic retry + backoff (survives free-tier 429 bursts)."""
    prompt = (
        f"SUBJECT: {subject}\n"
        f"FROM: {sender}\n"
        f"BODY:\n{(body or '')[:2500]}\n\n"
        "Classify this email and return the JSON object as specified."
    )
    last_err = ""
    for i in range(attempts):
        try:
            r = generate_json(prompt, system_instruction=SYSTEM)
            cat = r.get("category", "applied")
            if cat not in ("applied", "cold_offer"):
                cat = "applied"
            return {
                "is_job_related": bool(r.get("is_job_related", False)),
                "category": cat,
                "company_name": r.get("company_name") or "Unknown",
                "job_role": r.get("job_role") or "Unknown",
                "summary": r.get("summary", ""),
                "mail_summary": r.get("mail_summary", ""),
                "next_step": r.get("next_step", ""),
            }
        except Exception as e:
            last_err = f"{type(e).__name__}: {str(e)[:120]}"
            if i < attempts - 1:
                time.sleep(5 * (i + 1))   # 5s, then 10s backoff
    return {"is_job_related": None, "category": "applied",
            "company_name": "Unknown", "job_role": "Unknown",
            "summary": "", "mail_summary": "", "next_step": "",
            "error": last_err}