from core.gemini_client import generate_json

SYSTEM = """You are an expert career assistant that analyzes job-related emails.
Always return valid JSON only. No extra commentary."""


def _build_prompt(subject, sender, body):
    schema = """{
  "is_job_related": true/false,
  "category": "applied" OR "cold_offer" OR "not_job_related",
  "company_name": string,
  "job_role": string,
  "summary": string,
  "mail_summary": string,
  "next_step": string
}"""
    guidance = (
        "Field guidance:\n"
        "- category='applied': email responds to a job the candidate ALREADY applied to "
        "(application confirmation, interview invite after applying, offer/rejection tied to an application).\n"
        "- category='cold_offer': UNSOLICITED outreach/opportunity the candidate did NOT apply for "
        "('came across your profile', 'found your resume', 'are you open to opportunities').\n"
        "- category='not_job_related': spam, newsletters, personal, or non-job content.\n"
        "- company_name: the hiring company, or 'Unknown'.\n"
        "- job_role: the position, or 'Unknown'.\n"
        "- summary: 2-3 sentence AI summary about the ROLE and COMPANY.\n"
        "- mail_summary: 1-2 sentence summary of what THIS EMAIL specifically says.\n"
        "- next_step: ONE concrete recommended action for the candidate.\n"
    )
    prompt = (
        "Analyze the following email and return a JSON object with exactly these fields:\n\n"
        + schema + "\n\n"
        + guidance + "\n"
        + f"Email Subject: {subject}\n"
        + f"From: {sender}\n\n"
        + f"Email Body:\n{body}\n"
    )
    return prompt


def classify_email(subject, sender, body):
    prompt = _build_prompt(subject, sender, body)
    try:
        result = generate_json(prompt, system_instruction=SYSTEM)
        return result
    except Exception as e:
        return {
            "is_job_related": False,
            "category": "not_job_related",
            "company_name": "Unknown",
            "job_role": "Unknown",
            "summary": "",
            "mail_summary": "",
            "next_step": "",
            "_error": str(e),
        }