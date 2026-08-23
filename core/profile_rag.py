import os
import re
import json
import math
import hashlib
import datetime
import time
from core.embeddings import embed_text
from core.gemini_client import generate_json

DB_DIR = "db"
PROFILE_PATH = os.path.join(DB_DIR, "profile.json")
INDEX_PATH = os.path.join(DB_DIR, "profile_index.json")

HEADINGS = ["summary", "objective", "about", "skills", "technical skills",
            "experience", "work experience", "employment", "education",
            "projects", "certifications", "achievements", "internship"]


# ---------------------------------------------------------------- ingestion (unchanged)
def _norm(t):
    return re.sub(r"\s+", " ", t or "").strip()


def _is_heading(line):
    s = line.strip()
    if not s or len(s) > 60:
        return False
    low = s.lower().rstrip(":")
    return (low in HEADINGS
            or (len(s) < 40 and s.endswith(":"))
            or (s.isupper() and len(s) < 40))


def _section_of(heading):
    low = (heading or "").lower()
    for key in ("skill", "summary", "objective", "about", "internship",
                "experience", "education", "project", "certif", "achieve"):
        if key in low:
            return key
    return "other"


def chunk_profile(text):
    chunks = []
    cur_head, cur_lines = "general", []

    def flush():
        body = "\n".join(cur_lines).strip()
        cur_lines.clear()
        if not body:
            return
        if cur_head == "project":
        # one chunk per project entry (title line + its description)
            paras, buf = [], ""
            for ln in body.splitlines():
                s = ln.strip()
                if (s and not s.startswith(("•", "-", "*", "–"))
                        and re.match(r"^[A-Z0-9]", s) and ("–" in s or "—" in s or "-" in s)):
                    if buf:
                        paras.append(buf.strip())
                    buf = ln
                else:
                    buf = (buf + "\n" + ln).strip()
            if buf:
                paras.append(buf.strip())
            paras = paras or [body]
        else:
            paras = [p.strip() for p in re.split(r"\n{2,}", body) if p.strip()] or [body]

        buf = ""
        for p in paras:
            if buf and len(buf) + len(p) > 1200:
                chunks.append((cur_head, buf.strip()))
                buf = p
            else:
                buf = (buf + "\n\n" + p).strip()
        if buf:
            chunks.append((cur_head, buf.strip()))

    for line in (text or "").splitlines():
        if _is_heading(line):
            flush()
            cur_head = _section_of(line)
        else:
            cur_lines.append(line)
    flush()

    if not chunks and _norm(text):
        chunks = [("general", _norm(text)[:2000])]
    return [{"section": s, "text": t} for s, t in chunks]


# ---------------------------------------------------------------- storage (unchanged)
def save_profile(text, source="pasted", progress_cb=None):
    text = (text or "").strip()
    if not text:
        raise ValueError("Profile text is empty.")
    old_vecs = {c.get("hash"): c.get("vec") for c in get_index()}
    chunks = chunk_profile(text)

    # dedupe first so the progress total is accurate
    unique, seen = [], set()
    for c in chunks:
        h = hashlib.sha1(c["text"].encode("utf-8")).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append((h, c))

    index, new_embeds = [], 0
    total = len(unique)
    for n, (h, c) in enumerate(unique, 1):
        if progress_cb:
            progress_cb(n, total, c["section"])
        vec = old_vecs.get(h)              # reuse vector if chunk unchanged
        if vec is None:
            vec = embed_text(c["text"])
            new_embeds += 1
            time.sleep(0.2)
        index.append({
            "id": f"PC-{len(index) + 1:03d}",
            "section": c["section"],
            "text": c["text"],
            "hash": h,
            "vec": vec,
        })
    os.makedirs(DB_DIR, exist_ok=True)
    meta = {"uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": source, "chars": len(text), "chunks": len(index),
            "new_embeds": new_embeds}
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump({**meta, "text": text}, f, indent=2)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f)
    return meta


def append_profile(new_text, source="append", progress_cb=None):
    """Append new data (project / skill / certification) and re-index incrementally."""
    new_text = (new_text or "").strip()
    if not new_text:
        raise ValueError("Nothing to append.")
    prof = get_profile()
    base = (prof or {}).get("text", "").strip()
    full = (base + "\n\n" + new_text) if base else new_text
    return save_profile(full, source=source, progress_cb=progress_cb)

def get_profile():
    if not os.path.exists(PROFILE_PATH):
        return None
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_index():
    if not os.path.exists(INDEX_PATH):
        return []
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def has_profile():
    return bool(get_index())


def clear_profile():
    for p in (PROFILE_PATH, INDEX_PATH):
        try:
            os.remove(p)
        except Exception:
            pass


# ---------------------------------------------------------------- retrieval v2
def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def _tokenize(t):
    return re.findall(r"[a-z0-9+#]+", (t or "").lower())


class _BM25:
    """Tiny pure-Python Okapi BM25 — the sparse (exact keyword) scorer."""

    def __init__(self, docs):
        self.doc_tokens = [_tokenize(d) for d in docs]
        self.N = len(self.doc_tokens)
        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avgdl = (sum(self.doc_len) / self.N) if self.N else 1.0
        if not self.avgdl:
            self.avgdl = 1.0
        self.df = {}
        for toks in self.doc_tokens:
            for w in set(toks):
                self.df[w] = self.df.get(w, 0) + 1
        self.k1, self.b = 1.5, 0.75

    def score(self, q_tokens, i):
        toks = self.doc_tokens[i]
        if not toks:
            return 0.0
        tf = {}
        for w in toks:
            tf[w] = tf.get(w, 0) + 1
        s = 0.0
        for w in q_tokens:
            f = tf.get(w)
            if not f:
                continue
            dfw = self.df.get(w, 0)
            idf = math.log(1 + (self.N - dfw + 0.5) / (dfw + 0.5))
            s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl))
        return s


def _rrf(rankings, k=60):
    """Reciprocal Rank Fusion — merge multiple ranked lists fairly."""
    scores = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)


def distill_query(jd_text):
    """Sharpen a long JD into role + requirement lines so the query vector isn't diluted."""
    lines = (jd_text or "").splitlines()
    keys = ("role", "title", "skill", "require", "must", "experience",
            "proficien", "qualif", "responsib", "good to have")
    keep = []
    for ln in lines[:200]:
        low = ln.strip().lower()
        if low and len(low) <= 220 and any(kk in low for kk in keys):
            keep.append(ln.strip())
    head = " ".join(l.strip() for l in lines[:6] if l.strip())
    distilled = (head + " " + " ".join(keep)).strip()[:1500]
    return distilled or (jd_text or "").strip()[:1500]


def _llm_rerank(query, chunks):
    """Second-opinion judge: Gemini rates each candidate chunk 0-10."""
    items = [{"i": n, "section": c["section"], "text": c["text"][:600]}
             for n, c in enumerate(chunks)]
    prompt = (
        f"TARGET JOB:\n{(query or '')[:8000]}\n\n"
        f"CANDIDATE CHUNKS:\n{json.dumps(items, indent=1)}\n\n"
        "Rate how useful each chunk is as evidence for tailoring a resume to this job "
        "(0 = irrelevant, 10 = directly relevant)."
        '\nReturn JSON: {"scores":[{"i":number,"score":number}]}'
    )
    try:
        data = generate_json(prompt, system_instruction="You are a retrieval judge. Return valid JSON only.")
        lookup = {int(s.get("i", -1)): float(s.get("score", 0)) for s in data.get("scores", [])}
    except Exception:
        lookup = {}
    return [(n, lookup.get(n, 5.0)) for n in range(len(chunks))]


def search_profile(query, top_k=5, rerank=False):
    """Hybrid retrieval: dense cosine + BM25 keywords, fused with RRF; optional LLM rerank."""
    idx = get_index()
    if not idx:
        return []
    texts = [c["text"] for c in idx]

    # 1) dense (meaning) on the distilled query
    q_dist = distill_query(query)
    dense_rank, cos_by_i = [], {}
    try:
        qv = embed_text(q_dist)
        ds = []
        for i, c in enumerate(idx):
            s = _cos(qv, c["vec"])
            cos_by_i[i] = s
            ds.append((s, i))
        dense_rank = [i for _, i in sorted(ds, reverse=True)]
    except Exception:
        pass

    # 2) sparse (exact keywords) on raw + distilled query
    bm = _BM25(texts)
    qt = _tokenize(query) + _tokenize(q_dist)
    ss = [(bm.score(qt, i), i) for i in range(len(idx))]
    bm_by_i = {i: s for s, i in ss}
    sparse_rank = [i for _, i in sorted(ss, reverse=True)]

    # 3) fuse the two rankings
    fused = _rrf([r for r in (dense_rank, sparse_rank) if r])

    # intent-aware section boost: if the query asks for a foundation section that
    # is missing from the organic top-5, promote its best chunk into the candidates
    low = (query or "").lower()
    triggers = {
        "education": ("education", "degree", "qualif", "academic", "cgpa"),
        "skill": ("skill", "technolog", "stack"),
        "experience": ("experience", "employment", "work history"),
        "project": ("project", "portfolio"),
    }
    boost = []
    for sec, words in triggers.items():
        if any(w in low for w in words) and not any(idx[i]["section"] == sec for i in fused[:5]):
            for c in section_top(query, sec, 1):
                j = next((n for n, cc in enumerate(idx) if cc["text"] == c["text"]), None)
                if j is not None and j not in boost:
                    boost.append(j)
    if boost:
        fused = [i for i in fused if i not in boost]
        fused = boost + fused

    candidates = fused[: 12 if rerank else top_k]

    # 4) optional second-opinion rerank (premium path)
    if rerank and candidates:
        judged = _llm_rerank(query, [idx[i] for i in candidates])
        good = [(n, s) for n, s in judged if s >= 7]
        if len(good) < 3:
            good = sorted(judged, key=lambda t: t[1], reverse=True)[:3]
        good = sorted(good, key=lambda t: t[1], reverse=True)
        candidates = [candidates[n] for n, _ in good][:top_k]

    # 5) package results (displayed score = dense cosine when available)
    results = []
    mx = max(bm_by_i.values(), default=1.0) or 1.0
    for i in candidates[:top_k]:
        score = cos_by_i.get(i)
        if score is None:
            score = bm_by_i.get(i, 0.0) / mx
        results.append((round(float(score), 3), idx[i]))
    return results


def fit_score(job_text):
    res = search_profile(job_text, top_k=3)
    if not res:
        return None
    return round(max(0.0, min(100.0, 100 * sum(s for s, _ in res) / len(res))), 1)

def section_top(query, section, k=2):
    """Best chunks of ONE section for the query (BM25); always returns up to k."""
    idx = [c for c in get_index() if c.get("section") == section]
    if not idx:
        return []
    bm = _BM25([c["text"] for c in idx])
    qt = _tokenize(query)
    order = sorted(range(len(idx)), key=lambda i: bm.score(qt, i), reverse=True)
    # always return the first k chunks of this section (first = most important)
    return [idx[i] for i in order[:k]]