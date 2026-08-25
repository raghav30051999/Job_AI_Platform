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


# ---------------------------------------------------------------- contact (deterministic)
def _extract_contact(text):
    """Extract name/email/phone/location straight from the raw profile text.
    Model-independent: works for any resume, any AI model."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    name = email = phone = location = ""
    head = lines[:8]
    for l in head:
        if "@" in l or re.search(r"\d{6,}", l):
            continue
        words = l.split()
        if 2 <= len(words) <= 5 and len(l) <= 48 and re.match(r"^[A-Za-z][A-Za-z .,'-]+$", l):
            low = l.lower()
            if not any(k in low for k in ("summary", "objective", "resume",
                                          "curriculum", "vitae", "profile")):
                name = l.title() if l.isupper() else l
                break
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+\w", text or "")
    email = m.group(0) if m else ""
    m = re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text or "")
    phone = m.group(1).strip() if m else ""
    for l in head[1:]:
        if l == name or "@" in l or re.search(r"\d{6,}", l):
            continue
        if len(l) < 60 and re.search(r"(,|\bIndia\b)", l):
            location = l
            break
    return {"name": name, "email": email, "phone": phone, "location": location}


# ---------------------------------------------------------------- education (robust parse)
_DEGREE_KW = re.compile(
    r"(bachelor|master|b\.?tech|m\.?tech|b\.?e\b|m\.?e\b|b\.?sc|m\.?sc|bca|mca|mba|ph\.?d|"
    r"diploma|intermediate|ssc|cbse|icse|10th|12th|secondary|high school|"
    r"b\.?com|m\.?com|b\.?a\b|m\.?a\b|degree|qualification)", re.I)
_INST_KW = re.compile(
    r"(university|college|institute|institution|school|academy|campus)", re.I)
_SCORE_RE = re.compile(
    r"(CGPA|GPA|Percentage|Percent|Grade|Marks)\s*[:\-]?\s*([\d.]+)\s*%?", re.I)
_YEAR_RE = re.compile(r"\d{4}\s*[-–]\s*\d{4}")


def _norm_s(x):
    return re.sub(r"[^a-z0-9]+", " ", (x or "").lower()).strip()

def _extract_education_block(profile_text):
    """Pull the raw EDUCATION section straight from the saved profile text."""
    lines = (profile_text or "").split("\n")
    block, in_edu = [], False
    for ln in lines:
        s = ln.strip()
        up = s.upper()
        is_edu_head = (len(s) < 60 and (up == "EDUCATION" or up.startswith("EDUCATION")
                       or up in ("ACADEMIC QUALIFICATIONS", "EDUCATIONAL QUALIFICATIONS", "ACADEMICS")))
        is_other_head = (bool(s) and s == up and len(s) < 50
                         and not re.search(r"\d", s) and re.match(r"^[A-Z &/]+$", s))
        # ALL-CAPS degree/institution lines are CONTENT, not section boundaries
        if is_other_head and (_DEGREE_KW.search(s) or _INST_KW.search(s)):
            is_other_head = False
        if is_edu_head:
            in_edu = True
            continue
        if in_edu and is_other_head:
            break
        if in_edu:
            block.append(ln)
    return "\n".join(block)


def _fields_from_block(blk):
    """Detect degree/institution by KEYWORDS, not line position (format-agnostic)."""
    lines = [l.strip() for l in blk.splitlines() if l.strip()]
    degree = inst = ""
    for l in lines:
        if not degree and _DEGREE_KW.search(l):
            degree = l.rstrip(" ,|;-")
        elif not inst and _INST_KW.search(l):
            inst = l.rstrip(" ,|;-")
    if not degree and not inst and len(lines) == 1:
        parts = [p.strip() for p in re.split(r"[|,]", lines[0]) if p.strip()]
        for p in parts:
            if not degree and _DEGREE_KW.search(p):
                degree = p
            elif not inst and _INST_KW.search(p):
                inst = p
        if not degree and parts:
            degree = parts[0]
        if not inst and len(parts) > 1 and parts[1] != degree:
            inst = parts[1]
    # last resort for degree: first line that is NOT institution/score/year;
    # if none exists, leave degree EMPTY so the fragment merges complementarily
    if not degree and lines:
        for l in lines:
            if _INST_KW.search(l) or _SCORE_RE.match(l) or _YEAR_RE.search(l):
                continue
            degree = l
            break
    ym = _YEAR_RE.search(blk)
    sm = _SCORE_RE.search(blk)
    return {"degree": degree, "institution": inst,
            "year": ym.group(0) if ym else "",
            "score": sm.group(2) if sm else ""}


def _parse_edu_blocks(text):
    """A new entry starts only at a NEW degree-keyword line, or at a blank line
    after an already-COMPLETE entry — blank lines inside an entry never split it."""
    entries, cur = [], []
    has_deg = has_inst = False
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            if cur and has_deg and has_inst:
                entries.append("\n".join(cur))
                cur, has_deg, has_inst = [], False, False
            continue
        is_deg = bool(_DEGREE_KW.search(s))
        if cur and is_deg and has_deg:
            entries.append("\n".join(cur))
            cur, has_deg, has_inst = [], False, False
        cur.append(s)
        if is_deg:
            has_deg = True
        if _INST_KW.search(s):
            has_inst = True
    if cur:
        entries.append("\n".join(cur))
    return [_fields_from_block(b) for b in entries]


def _mergeable(a, b):
    da, ia = _norm_s(a["degree"]), _norm_s(a["institution"])
    db, ib = _norm_s(b["degree"]), _norm_s(b["institution"])
    if da and da == db and (not ia or not ib or ia == ib):
        return True
    if ia and ia == ib and (not da or not db or da == db):
        return True
    same_score = a["score"] and a["score"] == b["score"]
    same_year = a["year"] and a["year"] == b["year"]
    # strict complement: one holds degree, the other institution
    if (same_score or same_year) and ((not da) != (not db)) and ((not ia) != (not ib)):
        return True
    # one side incomplete, the other carries the missing half, same score
    if same_score and (da or db) and (ia or ib) and ((not da or not db) or (not ia or not ib)):
        return True
    return False


def _merge_into(a, b):
    for k in ("degree", "institution", "year", "score"):
        if not a[k]:
            a[k] = b[k]


def _final_education(draft, evidence):
    """Single source of truth for education: parse raw profile + evidence + model
    draft into canonical entries, then merge complementary fragments (no dupes)."""
    sources = [_extract_education_block((get_profile() or {}).get("text", "")),
               "\n".join(e.get("text", "") for e in evidence
                         if e.get("section") == "education")]
    candidates = []
    for src in sources:
        candidates += _parse_edu_blocks(src)
    for m in draft.get("education") or []:
        if isinstance(m, dict):
            candidates.append({k: str(m.get(k) or "") for k in
                               ("degree", "institution", "year", "score")})
        elif isinstance(m, str) and m.strip():
            candidates.append({"degree": m.strip(), "institution": "",
                               "year": "", "score": ""})

    out = []
    for c in candidates:
        if not (c["degree"] or c["institution"]):
            continue
        for o in out:
            if _mergeable(o, c):
                _merge_into(o, c)
                break
        else:
            out.append(dict(c))

    final, seen = [], set()
    for e in out:
        key = (_norm_s(e["degree"]), _norm_s(e["institution"]))
        if key in seen:
            continue
        seen.add(key)
        final.append(e)
    if not final:
        return _norm_education(draft.get("education") or [])
    return final


# ---------------------------------------------------------------- main pipeline
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

    # Deterministic contact: raw-profile extraction wins over AI blanks/"Unknown"
    contact = dict(draft.get("contact") or {})
    det = _extract_contact((get_profile() or {}).get("text", ""))
    for k, v in det.items():
        cur = str(contact.get(k) or "").strip()
        if v and (not cur or cur.lower() in ("unknown", "n/a", "none")):
            contact[k] = v

    return {
        "jd_hash": jd_hash(jd_text),
        "company": draft.get("company", "Unknown"),
        "role": draft.get("role", "Unknown"),
        "fit": fit,
        "contact": contact,
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