import os
import json
import datetime
import streamlit as st
from core.eval_rag import run_retrieval_eval, run_generation_eval, SAMPLE_JD


def _save_report(retrieval, generation):
    os.makedirs("db", exist_ok=True)
    with open(os.path.join("db", "eval_report.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                   "retrieval": retrieval, "generation": generation}, f, indent=2)


def render():
    st.markdown("<h2 style='margin:.5rem 0 1rem 0'>🧪 RAG Evaluation Lab</h2>",
                unsafe_allow_html=True)
    st.caption("Measures retrieval recall (v1 dense vs v2 hybrid vs v2+rerank), faithfulness, "
               "unsupported-claim rate, section coverage, latency and estimated cost. "
               "Nothing runs automatically — press a button to run an eval.")

    # ---------------- retrieval quality ----------------
    st.markdown("<h3 style='margin:1.2rem 0 .6rem 0'>🔎 Retrieval quality</h3>",
                unsafe_allow_html=True)
    if st.button("▶ Run retrieval eval", key="run_retrieval"):
        with st.spinner("Scoring 5 cases × 3 pipelines (embeddings + rerank)..."):
            rows = run_retrieval_eval()
        st.session_state["retrieval_rows"] = rows
        st.session_state["retrieval_at"] = datetime.datetime.now().strftime("%H:%M:%S")
        _save_report(rows, st.session_state.get("gen_eval"))

    rows = st.session_state.get("retrieval_rows")
    if rows:
        st.caption(f"Last run: {st.session_state.get('retrieval_at', '—')} · "
                   "values = keyword-Recall@5 / section-hit@5")
        table_rows = []
        agg = {"v1": [0.0, 0.0], "v2": [0.0, 0.0], "v2r": [0.0, 0.0]}
        for r in rows:
            table_rows.append({
                "case": r["case"],
                "v1 dense": f"{r['v1'][0]:.2f} / {r['v1'][1]:.1f}",
                "v2 hybrid": f"{r['v2'][0]:.2f} / {r['v2'][1]:.1f}",
                "v2 + rerank": f"{r['v2r'][0]:.2f} / {r['v2r'][1]:.1f}",
            })
            for k in agg:
                agg[k][0] += r[k][0]
                agg[k][1] += r[k][1]
        n = len(rows) or 1
        table_rows.append({
            "case": "AVERAGE",
            "v1 dense": f"{agg['v1'][0] / n:.2f} / {agg['v1'][1] / n:.1f}",
            "v2 hybrid": f"{agg['v2'][0] / n:.2f} / {agg['v2'][1] / n:.1f}",
            "v2 + rerank": f"{agg['v2r'][0] / n:.2f} / {agg['v2r'][1] / n:.1f}",
        })
        st.table(table_rows)
    else:
        st.caption("No retrieval eval yet — press the button above.")

    # ---------------- generation quality ----------------
    st.markdown("<h3 style='margin:1.2rem 0 .6rem 0'>📝 Generation quality (faithfulness audit)</h3>",
                unsafe_allow_html=True)
    jd = st.text_area("JD used for the generation audit", height=140,
                      key="eval_jd", value=SAMPLE_JD)
    if st.button("▶ Run generation eval", key="run_gen"):
        with st.spinner("Generating resume + auditing claims with Gemini judge..."):
            g = run_generation_eval(jd)
        st.session_state["gen_eval"] = g
        st.session_state["gen_at"] = datetime.datetime.now().strftime("%H:%M:%S")
        _save_report(st.session_state.get("retrieval_rows"), g)

    g = st.session_state.get("gen_eval")
    if g:
        if g.get("error"):
            st.warning(g["error"])
        else:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Faithfulness", f"{g['faithfulness']:.0%}")
            k2.metric("Section coverage", f"{g['section_coverage']:.0%}")
            k3.metric("Latency", f"{g['generation_seconds']}s")
            k4.metric("Est. cost", f"${g['est_cost_usd']}")
            st.caption(f"Last run: {st.session_state.get('gen_at', '—')} · "
                       f"{len(g['unsupported_claims'])} unsupported of {g['total_claims']} claims")
            if g["unsupported_claims"]:
                for u in g["unsupported_claims"]:
                    st.markdown(f"<div class='td-next' style='margin-bottom:.3rem'>⚠ {u}</div>",
                                unsafe_allow_html=True)
            else:
                st.success("No unsupported claims detected — resume fully grounded.")