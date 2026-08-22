import json
import re
import hashlib
from core.profile_rag import (search_profile, fit_score, has_profile,
                              get_profile, get_index, section_top)
from core.gemini_client import generate_json

SYSTEM = """You are an elite executive resume writer, ATS (Applicant Tracking System) specialist, and career coach.

CORE MISSION
Rewrite the candidate's REAL experience into a COMPLETE, submit-ready, ATS-friendly resume for the target job. Accuracy is more important than impressiveness; completeness is more important than brevity; honesty is non-negotiable.

GROUNDING RULES (STRICT)
1. Use ONLY facts present in the CANDIDATE PROFILE EVIDENCE. Never invent employers, job titles, dates, certifications, metrics, technologies, or responsibilities.
2. If a detail is not in the evidence, omit it — do not guess, do not pad, do not hallucinate.
3. Preserve original facts exactly: numbers, percentages, tool names, project names, dates, and organization names must match the evidence.
4. You may rephrase, reorder, and reframe evidence, and state transferable skills directly implied by it — but never fabricate new events.

COVERAGE RULES
5. EDUCATION: list EVERY education entry present in the evidence (university degree, intermediate, secondary/SSC, etc.), each with qualification name, institution, tenure years, and score/CGPA/percentage EXACTLY as given. NEVER omit any education entry.
6. PROJECTS: include each evidence project relevant to the JD as its own entry, name verbatim, 3-4 bullets covering tools and outcomes stated in the evidence.
7. EXPERIENCE: include the candidate's roles with official title, employer and dates verbatim; 4-5 bullets per role.
8. CONTACT: fill name/phone/email/location EXACTLY from the evidence header chunk; use "" for anything absent.
9. CERTIFICATIONS and LANGUAGES: include every item present in the evidence; [] if none.

STYLE RULES
10. Professional but SIMPLE voice — plain words, no jargon-stacking, no first-person pronouns, no clichés.
11. Past tense for completed work, present tense for the current role.
12. ATS-friendly: standard section names, plain structure, no tables/graphics/emojis/markdown inside field values.

HONESTY
13. "gaps" must list ONLY genuine mismatches between JD requirements and the evidence.

OUTPUT CONTRACT
14. Return ONE valid JSON object and nothing else — no markdown fences, no commentary.
15. Follow the exact schema requested in the user message. Use [] for any section with no truthful content."""

EDITOR_SYSTEM = """You are a ruthless executive resume editor. Rewrite the draft resume for impact, clarity, flow and ATS readability, using plain, direct, real-world language.
FROZEN FACTS: you may rephrase, reorder and tighten — but NEVER add, remove, or change any fact, number, tool, name, date, employer, degree, or skill. Preserve the full substance of every section. Preserve the honest framing of career transitions. NEVER drop any education entry.
Return ONE valid JSON object with the IDENTICAL schema."""


def jd_hash(jd_text):
    return hashlib.sha1((jd_text or "").strip().encode("utf-8")).hexdigest()[:12]


def _build_evidence(jd_text):
    hits = search_profile(jd_text, top_k=5, rerank=True)
    evidence = [{"section": c["section"], "text": c["text"], "score": round(float(s), 3)}
                for s, c in hits]
    have = {e["text"] for e in evidence}

    # Always include the header chunk (name/contact)
    idx = get_index()
    if idx and idx[0]["text"] not in have:
        evidence.append({"section": idx[0]["section"], "text": idx[0]["text"], "score": "core"})
        have.add(idx[0]["text"])

    # Education: pull ALL chunks unconditionally
    for c in get_index():
        if c.get("section") == "education" and c["text"] not in have:
            evidence.append({"section": "education", "text": c["text"], "score": "core"})
            have.add(c["text"])

    # Other sections: top-k as before
    for sec, k in (("skill", 2), ("experience", 2), ("project", 3)):
        for c in section_top(jd_text, sec, k):
            if len(evidence) >= 14:
                break
            if c["text"] not in have:
                evidence.append({"section": c["section"], "text": c["text"], "score": "core"})
                have.add(c["text"])
    flags = ["stockwatch", "hermes", "ocr pipeline", "insurance"]
    for c in get_index():
        if c["section"] == "project" and c["text"] not in have:
            if any(f in c["text"].lower() for f in flags):
                evidence.append({"section": "project", "text": c["text"], "score": "core"})
                have.add(c["text"])
                if len(evidence) >= 14:
                    break
    return evidence


def _detect_transition(jd_text, evidence):
    prompt = (
        f"JOB DESCRIPTION:\n{jd_text[:3000]}\n\n"
        f"CANDIDATE EVIDENCE:\n{json.dumps(evidence[:8], indent=1)}\n\n"
        "Analyze:\n"
        "1. What is the candidate's ACTUAL current/past role(s) and employer(s) from the evidence?\n"
        "2. What is the TARGET role from the JD?\n"
        "3. Do they differ significantly (e.g., non-IT → IT, government → corporate)?\n\n"
        'Return JSON: {"actual_role": str, "target_role": str, "is_transition": bool}'
    )
    try:
        data = generate_json(prompt, system_instruction="Return valid JSON only.")
        return (data.get("is_transition", False),
                data.get("actual_role", "Professional"),
                data.get("target_role", "AI Engineer"))
    except Exception:
        return (False, "Professional", "AI Engineer")


def _norm_education(items):
    """Map whatever keys/shape the model returns into canonical education entries."""
    out = []
    for e in items or []:
        if isinstance(e, str):
            if e.strip():
                out.append({"degree": e.strip(), "institution": "", "year": "", "score": ""})
            continue
        if not isinstance(e, dict):
            continue
        deg = (e.get("degree") or e.get("qualification") or e.get("title")
               or e.get("name") or "")
        inst = (e.get("institution") or e.get("college") or e.get("school")
                or e.get("board") or e.get("organization") or "")
        yr = (e.get("year") or e.get("years") or e.get("tenure")
              or e.get("period") or e.get("duration") or "")
        sc = (e.get("score") or e.get("cgpa") or e.get("gpa")
              or e.get("percentage") or e.get("marks") or "")
        out.append({"degree": str(deg), "institution": str(inst),
                    "year": str(yr), "score": str(sc)})
    return out


def _fill_education(resume, evidence):
    """Force every education entry from evidence chunks back into the resume.
    Bulletproof parser: splits by year-range patterns (most reliable marker)."""
    edu_text = "\n".join(e.get("text", "") for e in evidence
                         if e.get("section") == "education")
    if not edu_text.strip():
        return resume

    year_pattern = re.compile(r'(\d{4}\s*[-–]\s*\d{4})')
    segments = year_pattern.split(edu_text)

    entries_found = []
    for i in range(1, len(segments), 2):
        year = segments[i].strip()
        prev = segments[i - 1] if i > 0 else ""
        following = segments[i + 1] if i + 1 < len(segments) else ""

        prev_lines = [l.strip() for l in prev.split("\n") if l.strip()]
        degree_line = prev_lines[-1] if prev_lines else ""
        degree = re.sub(r'\s*\d{4}\s*[-–]\s*\d{4}.*$', '', degree_line).strip()
        degree = degree.strip()

        following_lines = [l.strip() for l in following.split("\n") if l.strip()]
        institution = ""
        score = ""
        for fl in following_lines:
            sm = re.search(r'(CGPA|Percentage|Grade|Marks)\s*[-–:]\s*([\d.]+)', fl, re.I)
            if sm:
                score = sm.group(2).strip()
            elif fl and not institution and not re.match(r'^(CGPA|Percentage|Grade|Marks)', fl, re.I):
                if not year_pattern.search(fl):
                    institution = fl

        if degree:
            entries_found.append({
                "degree": degree,
                "institution": institution,
                "year": year,
                "score": score,
            })

    out = list(resume.get("education") or [])
    seen = {(str(e.get("degree", "")).strip().lower(),
             str(e.get("institution", "")).strip().lower())
            for e in out}

    for f in entries_found:
        key = (f.get("degree", "").strip().lower(),
               f.get("institution", "").strip().lower())
        if key in seen:
            # If existing entry lacks score/year, fill it in
            for e in out:
                ek = (str(e.get("degree", "")).strip().lower(),
                      str(e.get("institution", "")).strip().lower())
                if ek == key:
                    if not e.get("score") and f.get("score"):
                        e["score"] = f.get("score")
                    if not e.get("year") and f.get("year"):
                        e["year"] = f.get("year")
            continue
        if not f.get("degree"):
            continue
        out.append({
            "degree": f.get("degree", ""),
            "institution": f.get("institution", ""),
            "year": f.get("year", ""),
            "score": f.get("score", ""),
        })
        seen.add(key)

    resume["education"] = out
    return resume

def _extract_education_block(profile_text):
    """Pull the raw EDUCATION section straight from the saved profile text."""
    import re as _re
    lines = (profile_text or "").split("\n")
    block, in_edu = [], False
    for ln in lines:
        s = ln.strip()
        up = s.upper()
        is_edu_head = (len(s) < 60 and (up == "EDUCATION" or up.startswith("EDUCATION")
                       or up in ("ACADEMIC QUALIFICATIONS", "EDUCATIONAL QUALIFICATIONS", "ACADEMICS")))
        is_other_head = (bool(s) and s == up and len(s) < 50
                         and not _re.search(r"\d", s) and _re.match(r"^[A-Z &/]+$", s))
        if is_edu_head:
            in_edu = True
            continue
        if in_edu and is_other_head:
            break
        if in_edu:
            block.append(ln)
    return "\n".join(block)


def _final_education(draft, evidence):
    """Ground-truth education. Reads the raw profile text first (guaranteed complete),
    then falls back to evidence/index chunks."""
    import re as _re

    def _norm_item(e):
        if isinstance(e, str):
            return {"degree": e.strip(), "institution": "", "year": "", "score": ""}
        return {
            "degree": str(e.get("degree") or e.get("qualification") or e.get("title") or e.get("name") or ""),
            "institution": str(e.get("institution") or e.get("college") or e.get("school") or e.get("board") or ""),
            "year": str(e.get("year") or e.get("years") or e.get("tenure") or e.get("period") or ""),
            "score": str(e.get("score") or e.get("cgpa") or e.get("gpa") or e.get("percentage") or e.get("marks") or ""),
        }

    def _parse(text):
        found = []
        if not text or not text.strip():
            return found
        year_pat = _re.compile(r"(\d{4}\s*[-–]\s*\d{4})")
        segs = year_pat.split(text)
        for i in range(1, len(segs), 2):
            year = segs[i].strip()
            prev_lines = [l.strip() for l in segs[i - 1].split("\n") if l.strip()]
            degree = prev_lines[-1] if prev_lines else ""
            degree = _re.sub(r"\s*\d{4}\s*[-–]\s*\d{4}.*$", "", degree).strip()
            following = segs[i + 1] if i + 1 < len(segs) else ""
            inst, score = "", ""
            for fl in [l.strip() for l in following.split("\n") if l.strip()]:
                sm = _re.search(r"(CGPA|Percentage|Grade|Marks)\s*[-–:]\s*([\d.]+)", fl, _re.I)
                if sm:
                    score = sm.group(2).strip()
                elif (fl and not inst
                      and not _re.match(r"^(CGPA|Percentage|Grade|Marks)", fl, _re.I)
                      and not year_pat.search(fl)):
                    inst = fl
            if degree:
                found.append({"degree": degree, "institution": inst,
                              "year": year, "score": score})
        return found

    # Layer 0 (primary): raw saved profile text — bypasses chunking/tagging entirely
    prof = get_profile() or {}
    parsed = _parse(_extract_education_block(prof.get("text", "")))

    # Fallbacks: evidence education chunks -> any evidence chunk -> any index chunk
    if not parsed:
        parsed = _parse("\n".join(e.get("text", "") for e in evidence
                                  if e.get("section") == "education"))
    if not parsed:
        for e in evidence:
            parsed += _parse(e.get("text", ""))
    if not parsed:
        for c in get_index():
            parsed += _parse(c.get("text", ""))

    # dedupe
    deduped, seen = [], set()
    for p in parsed:
        key = (p["degree"].lower(), p["institution"].lower(), p["year"])
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    parsed = deduped

    if not parsed:
        return [_norm_item(x) for x in (draft.get("education") or [])
                if isinstance(x, (dict, str))]

    out = list(parsed)
    seen = {(p["degree"].lower(), p["institution"].lower()) for p in parsed}
    for m in draft.get("education") or []:
        if not isinstance(m, dict):
            continue
        key = (str(m.get("degree", "")).lower(), str(m.get("institution", "")).lower())
        if key not in seen:
            out.append(m)
            seen.add(key)
    return [_norm_item(x) for x in out]


def tailor_for_jd(jd_text, force=False):
    jd_text = (jd_text or "").strip()
    if not jd_text:
        return {"error": "Paste a job description first."}
    if not has_profile():
        return {"error": "Upload your profile first (👤 My Profile above)."}

    evidence = _build_evidence(jd_text)
    fit = fit_score(jd_text)

    is_transition, actual_role, target_role = _detect_transition(jd_text, evidence)

    if is_transition:
        framing_instruction = (
            f"CAREER TRANSITION DETECTED:\n"
            f"- Actual role: {actual_role}\n"
            f"- Target role: {target_role}\n\n"
            f"SUMMARY MUST:\n"
            f"- Start with: '{actual_role} with [X] years of hands-on, self-driven experience in [target field]...'\n"
            f"- Or: '{actual_role} transitioning into [target field]...'\n"
            f"- Frame all technical work as self-driven initiatives, not official job duties.\n\n"
            f"FORBIDDEN IN SUMMARY:\n"
            f"- 'AI Engineer with X years of experience...'\n"
            f"- '[Target Role] with X years of experience...'\n"
            f"- Any phrasing that implies formal employment in the target role.\n\n"
        )
    else:
        framing_instruction = "No career transition detected — frame normally.\n\n"

    prompt = (
        f"JOB DESCRIPTION (raw):\n{jd_text[:12000]}\n\n"
        f"CANDIDATE PROFILE EVIDENCE (ranked; 'core' = always-included foundation):\n"
        f"{json.dumps(evidence, indent=1)}\n\n"
        f"{framing_instruction}"
        "Task: Create a COMPLETE, submit-ready, ATS-friendly resume tailored for THIS job.\n\n"
        "Instructions:\n"
        "1. Extract 'company' and 'role' from the JD (use 'Unknown' if not stated).\n"
        "2. contact: name/phone/email/location exactly from the evidence header chunk ('' if absent).\n"
        "3. headline: '<target role> | <top 2-3 evidence-backed strengths>'.\n"
        "4. summary: 3-4 sentences following the framing rules above. Every claim must map to evidence.\n"
        "5. skills: 10-14 hard/technical skills present in BOTH evidence and JD territory.\n"
        "6. experience: official title/employer/dates verbatim. For NON-IT roles, phrase every bullet as a self-driven initiative solving a real problem ('Built X to automate Y using Z, eliminating manual effort'). 4-5 plain-language bullets each.\n"
        "7. projects: EVERY relevant evidence project, name verbatim; 3-4 plain-language bullets each (problem -> tool -> outcome).\n"
        "8. education: EVERY education entry in the evidence (B.Tech AND Intermediate AND SSC/secondary), each with degree (qualification name), institution, year (tenure), score (CGPA/percentage) exactly as given.\n"
        "9. certifications: every certification in evidence, else [].\n"
        "10. languages: every language in evidence, else [].\n"
        "11. gaps: 1-2 honest watch-outs, or [].\n\n"
        'Return JSON strictly in this shape:\n'
        '{"company": str, "role": str, '
        '"contact": {"name": str, "phone": str, "email": str, "location": str}, '
        '"headline": str, "summary": str, "skills": [str], '
        '"experience": [{"title": str, "company": str, "dates": str, "bullets": [str]}], '
        '"projects": [{"name": str, "bullets": [str]}], '
        '"education": [{"degree": str, "institution": str, "year": str, "score": str}], '
        '"certifications": [str], "languages": [str], "gaps": [str]}'
    )
    draft = generate_json(prompt, system_instruction=SYSTEM)

    # editor polish pass with frozen facts
    try:
        edited = generate_json(
            "DRAFT RESUME JSON:\n" + json.dumps(draft, indent=1) +
            "\n\nReturn the fully edited resume as ONE JSON object with the identical schema.",
            system_instruction=EDITOR_SYSTEM)
        if isinstance(edited, dict) and edited.get("summary") and edited.get("skills"):
            for k, v in draft.items():
                edited.setdefault(k, v)
            draft = edited
    except Exception:
        pass

    # Deterministic safety net: ensure no education entry was dropped
    draft = _fill_education(draft, evidence)

    return {
        "jd_hash": jd_hash(jd_text),
        "company": draft.get("company", "Unknown"),
        "role": draft.get("role", "Unknown"),
        "fit": fit,
        "contact": draft.get("contact", {}),
        "headline": draft.get("headline", ""),
        "summary": draft.get("summary", ""),
        "skills": draft.get("skills", []),
        "experience": draft.get("experience", []),
        "projects": draft.get("projects", []),
        "education": _final_education(draft, evidence),
        "certifications": draft.get("certifications", []),
        "languages": draft.get("languages", []),
        "gaps": draft.get("gaps", []),
        "evidence": evidence,
        "is_transition": is_transition,
    }