from core.gemini_client import generate_json

SYSTEM = """You are an expert email classifier for a job-seeking assistant.

Your task: determine if an email is JOB-RELATED and extract structured data if it is.

JOB-RELATED EMAILS INCLUDE (not exhaustive):
1. Job postings / vacancy announcements
2. Application confirmations ("we received your application")
3. Shortlist notifications ("your resume has been shortlisted")
4. Interview invitations (virtual/in-person, with date/time)
5. Interview rescheduling / confirmation
6. Job offers / offer letters
7. Rejection letters ("we regret to inform you")
8. Recruiter outreach for specific roles
9. Assessment / test invitations for job applications
10. Onboarding / next-step instructions after interview

NOT JOB-RELATED:
- Newsletters / marketing emails
- System notifications unrelated to jobs
- Spam / promotional content
- Generic "we're hiring" ads without specific role info
- Password resets / account notifications (unless job-platform specific)

OUTPUT CONTRACT:
Return ONE valid JSON object with these fields:
{
  "is_job_related": true/false,
  "category": "applied" | "cold_offer" | "interview" | "offer" | "rejection" | "other",
  "company_name": "Extracted company name or Unknown",
  "job_role": "Extracted role/title or Unknown",
  "summary": "1-2 sentence summary of the job/opportunity",
  "mail_summary": "1 sentence summary of what this email says",
  "next_step": "Actionable next step for the candidate"
}

Rules:
- If is_job_related is false, return minimal JSON: {"is_job_related": false, "category": "not_job_related", "company_name": "", "job_role": "", "summary": "", "mail_summary": "", "next_step": ""}
- Extract company from sender domain or email signature (e.g., "Salesforce India" from "HR Manager, Salesforce India")
- Extract role from subject or body (e.g., "Data Analyst")
- next_step should be actionable: "Attend interview on [date]", "Apply by [deadline]", "Reply to confirm", etc.
- Be conservative: if unsure, mark as not_job_related rather than guessing."""


def classify_email(subject, sender, body):
    """Classify an email and extract job-related metadata."""
    prompt = (
        f"SUBJECT: {subject}\n"
        f"FROM: {sender}\n"
        f"BODY:\n{body[:2500]}\n\n"
        "Classify this email and return JSON as specified in your instructions."
    )
    
    try:
        result = generate_json(prompt, system_instruction=SYSTEM)
        # Ensure required fields exist
        return {
            "is_job_related": result.get("is_job_related", False),
            "category": result.get("category", "other"),
            "company_name": result.get("company_name", "Unknown"),
            "job_role": result.get("job_role", "Unknown"),
            "summary": result.get("summary", ""),
            "mail_summary": result.get("mail_summary", ""),
            "next_step": result.get("next_step", ""),
        }
    except Exception as e:
        # Fallback: if classification fails, mark as not_job_related
        return {
            "is_job_related": False,
            "category": "classification_error",
            "company_name": "Unknown",
            "job_role": "Unknown",
            "summary": f"Classification failed: {str(e)}",
            "mail_summary": "",
            "next_step": "",
        }