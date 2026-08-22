import os
import json
import math
import time
import datetime

from core.embeddings import embed_text
from core.profile_rag import (get_index, search_profile, _cos,
                              _BM25, _tokenize, section_top)
from core.resume_tailor import tailor_for_jd
from core.gemini_client import generate_json

# approx Gemini Flash pricing (USD per 1M tokens) — tune to your tier
COST_IN, COST_OUT = 0.30, 2.50

SAMPLE_JD = (
    "Data Scientist — build predictive models for conversion, retention and churn; "
    "cluster hundreds of thousands of agent trajectories; extract insight from "
    "unstructured text (LLM traces, tickets, prompts); strong SQL, pandas, "
    "scikit-learn; embeddings and vector search; A/B testing and causal inference."
)

# optional hand-labeled cases; auto cases are added ON TOP of these
MANUAL_CASES = []

STOP = {"the", "and", "for", "with", "a", "an", "in", "of", "to", "on", "is", "are",
        "or", "at", "by", "from", "as", "into", "etc", "using", "used", "that",
        "this", "it", "its", "be", "been", "was", "were", "not", "no", "can", "will",
        "via", "per", "our", "your", "you", "we", "they", "them", "his", "her",
        "has", "have", "had", "who", "what", "when", "where", "how", "all", "any", "each"}

SECTION_QUERIES = {
    "skill": "Candidate core technical skills, tools and technologies",
    "experience": "Candidate professional work experience and job roles",
    "project": "Candidate independent projects and implementations",
    "education": "Candidate academic qualifications, degrees and certifications",
}


# ---------------------------------------------------------------- auto-labeling
def _distinctive_tokens(chunks, bm_all, top=4):
    """Highest-IDF tokens of these chunks = automatic gold keywords."""
    scores = {}
    for c in chunks:
        tf = {}
        for w in _tokenize(c["text"]):
            tf[w] = tf.get(w, 0) + 1
        for w, f in tf.items():
            if len(w) < 3 or w in STOP:
                continue
            dfw = bm_all.df.get(w, 0)
            idf = math.log(1 + (bm_all.N - dfw + 0.5) / (dfw + 0.5))
            scores[w] = scores.get(w, 0.0) + idf * f
    return sorted(scores, key=scores.get, reverse=True)[:top]


def build_cases():
    """One auto-labeled retrieval case per section present in the index."""
    idx = get_index()
    if not idx:
        return []
    bm_all = _BM25([c["text"] for c in idx])
    cases = []
    for sec, query in SECTION_QUERIES.items():
        sec_chunks = [c for c in idx if c["section"] == sec]
        if not sec_chunks:
            continue
        expected = section_top(query, sec, 2) or sec_chunks[:2]
        kws = _distinctive_tokens(expected, bm_all, top=4)
        if kws:
            cases.append({"name": f"[auto] {sec}", "query": query,
                          "keywords": kws, "sections": [sec]})
    return cases


# ---------------------------------------------------------------- retrieval
def _dense_only(query, k=5):
    """v1 baseline: pure cosine retrieval."""
    idx = get_index()
    if not idx:
        return []
    qv = embed_text(query)
    scored = sorted(((_cos(qv, c["vec"]), c) for c in idx),
                    key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:k]]


def _recall_keywords(chunks, keywords):
    blob = " ".join(c["text"] for c in chunks).lower()
    if not keywords:
        return 1.0
    return sum(1 for kw in keywords if kw.lower() in blob) / len(keywords)


def _section_hit(chunks, sections):
    have = {c["section"] for c in chunks}
    if not sections:
        return 1.0
    return sum(1 for s in sections if s in have) / len(sections)


def run_retrieval_eval(k=5):
    rows = []
    for case in MANUAL_CASES + build_cases():
        q = case["query"]
        v1 = _dense_only(q, k)
        v2 = [c for _, c in search_profile(q, top_k=k, rerank=False)]
        v2r = [c for _, c in search_profile(q, top_k=k, rerank=True)]
        rows.append({
            "case": case["name"],
            "v1": (_recall_keywords(v1, case["keywords"]), _section_hit(v1, case["sections"])),
            "v2": (_recall_keywords(v2, case["keywords"]), _section_hit(v2, case["sections"])),
            "v2r": (_recall_keywords(v2r, case["keywords"]), _section_hit(v2r, case["sections"])),
        })
    return rows


# ---------------------------------------------------------------- generation
def run_generation_eval(jd_text):
    t0 = time.perf_counter()
    res = tailor_for_jd(jd_text, force=True)
    gen_s = time.perf_counter() - t0
    if res.get("error"):
        return {"error": res["error"]}

    ev = {e["section"] for e in res["evidence"]}
    present = [1 for field, sec in (("experience", "experience"), ("projects", "project"),
                                    ("education", "education"), ("skills", "skill"))
               if res.get(field) and sec in ev]
    needed = [1 for field in ("experience", "projects", "education", "skills") if res.get(field)]
    coverage = round(sum(present) / len(needed), 2) if needed else 1.0

    audit = generate_json(
        "EVIDENCE CHUNKS:\n" + json.dumps(res["evidence"], indent=1) +
        "\n\nGENERATED RESUME:\n" + json.dumps(
            {k: res.get(k) for k in ("headline", "summary", "skills",
                                     "experience", "projects", "education")}, indent=1) +
        "\n\nCount every distinct factual claim in the resume (tools, numbers, employers, "
        "dates, project names, degrees). List the ones NOT supported by the evidence.\n"
        "CALIBRATION RULES:\n"
        "- The target job title appearing in the headline is the role being applied for; "
        "do NOT count it as a claim.\n"
        "- A claim is SUPPORTED if directly stated OR a conservative, narrower rephrasing "
        "of the evidence.\n"
        "- Count as unsupported ONLY claims that ADD new facts (tools, metrics, employers, "
        "dates, qualifications) absent from the evidence."
        '\nReturn JSON: {"total_claims": number, "unsupported": [string]}',
        system_instruction="You are a strict audit judge. Return valid JSON only.")
    total = max(1, int(audit.get("total_claims", 1) or 1))
    uns = audit.get("unsupported", []) or []

    in_tok = (len(jd_text) + sum(len(e["text"]) for e in res["evidence"])) / 4 + 700
    out_tok = len(json.dumps(res)) / 4
    cost = (in_tok / 1e6) * COST_IN + (out_tok / 1e6) * COST_OUT

    return {
        "generation_seconds": round(gen_s, 1),
        "total_claims": total,
        "unsupported_claims": uns,
        "unsupported_rate": round(len(uns) / total, 2),
        "faithfulness": round(1 - len(uns) / total, 2),
        "section_coverage": coverage,
        "est_cost_usd": round(cost, 5),
    }


# ---------------------------------------------------------------- report
def run_all(jd_text=None):
    jd_text = jd_text or SAMPLE_JD
    print("\n================= RAG EVALUATION =================")

    rows = run_retrieval_eval()
    print("\n-- RETRIEVAL  (keyword-Recall@5 / section-hit@5) --")
    print(f"{'case':<36}{'v1 dense':>12}{'v2 hybrid':>12}{'v2+rerank':>12}")
    agg = {"v1": [0, 0], "v2": [0, 0], "v2r": [0, 0]}
    for r in rows:
        print(f"{r['case']:<36}"
              f"{r['v1'][0]:>5.2f}/{r['v1'][1]:<4.1f}"
              f"{r['v2'][0]:>5.2f}/{r['v2'][1]:<4.1f}"
              f"{r['v2r'][0]:>5.2f}/{r['v2r'][1]:<4.1f}")
        for key in agg:
            agg[key][0] += r[key][0]
            agg[key][1] += r[key][1]
    n = len(rows) or 1
    print(f"{'AVERAGE':<36}"
          f"{agg['v1'][0]/n:>5.2f}/{agg['v1'][1]/n:<4.1f}"
          f"{agg['v2'][0]/n:>5.2f}/{agg['v2'][1]/n:<4.1f}"
          f"{agg['v2r'][0]/n:>5.2f}/{agg['v2r'][1]/n:<4.1f}")

    print("\n-- GENERATION (faithfulness / coverage / latency / cost) --")
    g = run_generation_eval(jd_text)
    if g.get("error"):
        print("generation error:", g["error"])
    else:
        print(f"faithfulness          : {g['faithfulness']:.0%} "
              f"({len(g['unsupported_claims'])} unsupported of {g['total_claims']} claims)")
        for u in g["unsupported_claims"]:
            print(f"   ⚠ unsupported: {u}")
        print(f"section coverage      : {g['section_coverage']:.0%}")
        print(f"end-to-end latency    : {g['generation_seconds']}s")
        print(f"estimated cost        : ${g['est_cost_usd']}")

    report = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
              "retrieval": rows, "generation": g}
    os.makedirs("db", exist_ok=True)
    with open(os.path.join("db", "eval_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\nreport saved to db/eval_report.json")


if __name__ == "__main__":
    run_all()