import math
import datetime
import streamlit as st
import plotly.graph_objects as go
from core.job_store import get_jobs, update_job, delete_by_ids
from core.job_sync import sync_now, STATUS
from core.settings import get_scan_since
from core.smtp_sender import send_test_email
from core.recommender import get_recommendations
from core.profile_rag import has_profile
from core.dedup import collapse_duplicates


BLUE, AMBER, NAVY = "#2563EB", "#F59E0B", "#16324F"
GRID, MUTED = "#E7EDF5", "#68788C"
FONT = "Geist, -apple-system, 'Segoe UI', sans-serif"


def _clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v)


def _disp(job):
    return {**job, **job.get("edited", {})}


def _set_all(master_key, sel_keys):
    val = st.session_state.get(master_key, False)   # .get -> no KeyError on fresh sessions
    for k in sel_keys:
        st.session_state[k] = val


def _spacer(h="1.5rem"):
    st.markdown(f'<div style="height:{h}"></div>', unsafe_allow_html=True)


def _kpi(icon, label, value, color):
    st.markdown(
        f'<div class="kpi" style="border-top:4px solid {color};">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span class="kpi-label">{label}</span>'
        f'<span style="font-size:1.25rem">{icon}</span>'
        f'</div>'
        f'<div class="kpi-value" style="color:{color};">{value}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _chart_header(title, subtitle=""):
    st.markdown(
        f'<div style="padding:.4rem .2rem 1rem .2rem;">'
        f'<div style="font-size:1.02rem;font-weight:700;color:{NAVY};">{title}</div>'
        f'<div style="font-size:.8rem;color:{MUTED};margin-top:.2rem;">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _donut(a, c):
    total = a + c
    if total == 0:
        fig = go.Figure()
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=280,
            paper_bgcolor="#FFFFFF",
            font=dict(color="#33475B", size=18, family=FONT),
            annotations=[dict(
                text="No opportunities yet",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=18, color=MUTED, family=FONT),
            )],
        )
        return fig

    fig = go.Figure(go.Pie(
        labels=["Applied", "Cold Offers"],
        values=[a, c],
        hole=0.62,
        marker=dict(colors=[BLUE, AMBER], line=dict(color="#FFFFFF", width=2)),
        textinfo="percent",
        textposition="inside",
        insidetextorientation="horizontal",
        textfont=dict(size=12, color="#FFFFFF"),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=500,
        paper_bgcolor="#FFFFFF",
        font=dict(color="#33475B", size=13, family=FONT),
        hoverlabel=dict(bgcolor="#16324F", font_color="#FFFFFF",
                        font_size=18, font_family=FONT),
        legend=dict(orientation="h", x=0.5, y=-0.08, xanchor="center",
                    font=dict(size=18, color=MUTED), itemsizing="constant"),
        annotations=[
            dict(text=f"<b>{total}</b>", x=0.5, y=0.54, showarrow=False,
                 font=dict(size=24, color=NAVY, family=FONT)),
            dict(text="Total", x=0.5, y=0.42, showarrow=False,
                 font=dict(size=18, color=MUTED, family=FONT)),
        ],
    )
    return fig


def _timeline(pairs):
    email_dates = [d["date"][:10] for _, d in pairs]
    today = datetime.date.today()
    last_10_days = [
        (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(9, -1, -1)
    ]
    labels = []
    counts = []
    for day in last_10_days:
        try:
            labels.append(datetime.datetime.strptime(day, "%Y-%m-%d").strftime("%b %d"))
        except Exception:
            labels.append(day)
        counts.append(email_dates.count(day))

    fig = go.Figure(go.Bar(
        x=labels,
        y=counts,
        marker=dict(color=BLUE, cornerradius=6),
        hovertemplate="%{x}<br>%{y} job email(s)<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=500,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        bargap=0.35,
        showlegend=False,
        font=dict(color="#33475B", size=18, family=FONT),
        hoverlabel=dict(bgcolor="#16324F", font_color="#FFFFFF",
                        font_size=18, font_family=FONT),
        xaxis=dict(showgrid=False, tickfont=dict(size=14, color=MUTED), fixedrange=True),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, dtick=1,
                   rangemode="tozero", tickfont=dict(size=14, color=MUTED),
                   fixedrange=True),
    )
    return fig


def _inline_editor(mid, d):
    jid = d["id"]                      # ← use JOB-id everywhere (matches the row's key)
    st.divider()
    st.caption(f"Received: {d['date']}")
    e1, e2, e3 = st.columns(3)
    ec = e1.text_input("Company", value=d["company_name"], key=f"ec_{jid}")
    er = e2.text_input("Job role", value=d["job_role"], key=f"er_{jid}")
    ecat = e3.selectbox("Section", ["applied", "cold_offer"],
                        index=0 if d["category"] == "applied" else 1, key=f"ecat_{jid}")
    en = st.text_input("Next step", value=d["next_step"], key=f"en_{jid}")
    nt = st.text_area("Custom notes", value=d.get("notes", ""), key=f"nt_{jid}", height=70)
    s1, s2, _ = st.columns([1, 1, 6])
    if s1.button("💾 Save", key=f"save_{jid}"):
        update_job(mid, {"notes": nt, "edited": {
            "company_name": _clean(ec), "job_role": _clean(er),
            "next_step": _clean(en), "category": _clean(ecat) or "applied"}})
        st.session_state[f"editing_{jid}"] = False
        st.rerun()
    if s2.button("Cancel", key=f"cancel_{jid}"):
        st.session_state[f"editing_{jid}"] = False
        st.rerun()


def _job_row(mid, d):
    st.markdown("<hr class='row-line'>", unsafe_allow_html=True)
    c = st.columns([0.5, 1, 1.8, 1.8, 3, 3, 2.2, 1.2], vertical_alignment="center")
    c[0].checkbox(f"Select {d['id']}", key=f"sel_{d['id']}", label_visibility="collapsed")
    c[1].markdown(f"<div class='td-id'>{d['id']}</div>", unsafe_allow_html=True)
    c[2].markdown(f"<div class='td'>{d['sender']}</div>", unsafe_allow_html=True)
    if d.get("dup_count"):
        c[3].markdown(
            f"<div class='td'>{d['job_role']} "
            f"<span style='background:#FEF3C7; color:#92400E; padding:1px 6px; "
            f"border-radius:10px; font-size:0.7rem; font-weight:600; margin-left:6px;'>"
            f"×{d['dup_count']}</span></div>", 
            unsafe_allow_html=True)
    else:
        c[3].markdown(f"<div class='td'>{d['job_role']}</div>", unsafe_allow_html=True)
    c[4].markdown(f"<div class='td-summary'>{d.get('mail_summary', '')}</div>", unsafe_allow_html=True)
    c[5].markdown(f"<div class='td-summary'>{d['summary']}</div>", unsafe_allow_html=True)
    c[6].markdown(f"<div class='td-next'>➤ {d.get('next_step', '')}</div>", unsafe_allow_html=True)

    a1, a2 = c[7].columns(2, gap="small")
    if a1.button("✏️", key=f"editbtn_{d['id']}", help="Edit this row"):
        editing_key = f"editing_{d['id']}"
        st.session_state[editing_key] = not st.session_state.get(editing_key, False)
    confirm_key = f"confirm_{d['id']}"
    if st.session_state.get(confirm_key):
        if a2.button("❗", key=f"delbtn_{d['id']}", help="Click again to confirm"):
            delete_by_ids([d["id"]])
            st.session_state.pop(confirm_key, None)
            st.rerun()
    else:
        if a2.button("🗑️", key=f"delbtn_{d['id']}", help="Delete this row"):
            st.session_state[confirm_key] = True
    if st.session_state.get(f"editing_{d['id']}"):
        _inline_editor(mid, d)


def _table_section(label, icon, pairs, key, color):
    st.markdown(
        f"<h3 style='margin:1.6rem 0 .7rem 0'>{icon} {label}"
        f"<span class='pill' style='background:{color}22;color:{color}'>{len(pairs)}</span></h3>",
        unsafe_allow_html=True)
    if not pairs:
        st.caption("Nothing here yet — send a test email above.")
        return

    ids = [d["id"] for _, d in pairs]

    if st.session_state.pop(f"del_sel_{key}", False):
        chosen = [i for i in ids if st.session_state.get(f"sel_{i}")]
        if chosen:
            delete_by_ids(chosen)
        for i in ids:
            st.session_state[f"sel_{i}"] = False
        st.session_state[f"select_all_{key}"] = False
        st.rerun()

    t1, t2 = st.columns([8.5, 1.5], vertical_alignment="center")
    t1.checkbox("Select all", key=f"select_all_{key}",
                on_change=_set_all, args=(f"select_all_{key}", [f"sel_{i}" for i in ids]))
    t2.button("🗑️ Delete selected", key=f"del_sel_{key}", width="stretch")

    with st.container(border=True):
        h = st.columns([0.5, 1, 1.8, 1.8, 3, 3, 2.2, 1.2], vertical_alignment="center")
        h[0].markdown("<div class='th'></div>", unsafe_allow_html=True)
        h[1].markdown("<div class='th'>ID</div>", unsafe_allow_html=True)
        h[2].markdown("<div class='th'>Mail Received From</div>", unsafe_allow_html=True)
        h[3].markdown("<div class='th'>Role Offered</div>", unsafe_allow_html=True)
        h[4].markdown("<div class='th'>Summary of Mail</div>", unsafe_allow_html=True)
        h[5].markdown("<div class='th'>AI Summary about the Company</div>", unsafe_allow_html=True)
        h[6].markdown("<div class='th'>Next Step</div>", unsafe_allow_html=True)
        h[7].markdown("<div class='th' style='text-align:center'>Actions</div>", unsafe_allow_html=True)
        for mid, d in pairs:
            _job_row(mid, d)


def _recommendation_section():
    prof_on = has_profile()
    personal = bool(st.session_state.get("reco_personal", False)) and prof_on
    mode = ("personalized", "#1B7F3B") if personal else ("generic mode", "#B45309")

    st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
    head, tog = st.columns([6, 3], vertical_alignment="center")
    head.markdown(
        "<h3 style='margin:0 0 .4rem 0'>AI Based recommendation:"
        "<span class='pill' style='background:#2563EB22;color:#2563EB'>beta</span>"
        f"<span class='pill' style='background:{mode[1]}22;color:{mode[1]}'>{mode[0]}</span></h3>",
        unsafe_allow_html=True)
    tog.toggle("Personalized mode", disabled=not prof_on, key="reco_personal",
               help="Rank opportunities using your uploaded profile. "
                    "To enable this mode, update the user profile in the Resume Designer page.")
    if not prof_on:
        st.caption("Personalized mode is locked — upload your profile in 📄 Resume Designer to unlock it.")

    reco = get_recommendations(personal=personal)
    if not reco:
        st.caption("Sync some job emails first — the Copilot will rank your best opportunities here.")
        return

    with st.container(border=True):
        top = st.columns([6, 2, 2], vertical_alignment="center")
        top[0].markdown(f"<div class='td-summary'>💡 {reco.get('strategy', '')}</div>",
                        unsafe_allow_html=True)
        top[1].caption(f"Generated: {reco.get('generated_at', '—')}")
        if top[2].button("🔄 Refresh", width="stretch", key="reco_refresh"):
            get_recommendations(force=True, personal=personal)
            st.rerun()

        # priority-based light fills: same priority = same color
        FILLS = {
            "high":   ("#FFF7ED", "#EA580C"),
            "medium": ("#EFF6FF", "#2563EB"),
            "low":    ("#F8FAFC", "#94A3B8"),
        }

        picks = reco.get("picks", [])
        st.markdown(
            "<div style='display:flex;gap:.6rem;margin:.4rem 0 .6rem 0;'>"
            "<span class='pill' style='background:#FFF7ED;color:#EA580C;border:1px solid #EA580C55;margin:0'>High</span>"
            "<span class='pill' style='background:#EFF6FF;color:#2563EB;border:1px solid #2563EB55;margin:0'>Medium</span>"
            "<span class='pill' style='background:#F8FAFC;color:#64748B;border:1px solid #94A3B855;margin:0'>Low</span>"
            "</div>", unsafe_allow_html=True)
        for i, p in enumerate(picks):
            pr = str(p.get("priority", "medium")).lower()
            bg, border = FILLS.get(pr, FILLS["medium"])
            match_txt = f" · {p.get('match')}% match" if p.get("match") is not None else ""
            st.markdown(
                f"<div style='background:{bg};border:1px solid {border}55;"
                f"border-left:5px solid {border};border-radius:12px;"
                f"padding:.8rem 1.1rem;margin-bottom:.7rem;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span class='kpi-label'>#{i + 1} · {p.get('priority', 'Medium')}{match_txt}</span>"
                f"<span class='mono' style='color:#2563EB;font-weight:700;font-size:.75rem'>"
                f"{p.get('id', '')}</span></div>"
                f"<div style='font-weight:800;color:#16324F;margin-top:.15rem'>"
                f"{p.get('company', 'Unknown')} "
                f"<span style='font-weight:500;color:#44566C'>— {p.get('role', '')}</span></div>"
                f"<div class='td-summary' style='margin-top:.3rem'>{p.get('reason', '')}</div>"
                f"</div>",
                unsafe_allow_html=True)

        kw = reco.get("keywords", [])
        if kw:
            st.markdown("<div class='th' style='margin-top:1rem'>Resume keywords to highlight</div>",
                        unsafe_allow_html=True)
            pills = "".join(
                f"<span class='pill' style='background:#2563EB18;color:#2563EB;"
                f"margin:0 .5rem .5rem 0'>{k}</span>" for k in kw)
            st.markdown(f"<div style='padding-bottom:.6rem'>{pills}</div>",
                        unsafe_allow_html=True)


def render():
    st.markdown("""
    <style>
    /* 1) precise: bordered wrapper that contains table cells */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.td-id),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.th){
      background:#FFFFFF !important;
      border:1px solid #E3EAF3 !important;
      border-radius:16px !important;
      box-shadow:0 2px 10px rgba(16,50,80,.06) !important;
    }
    /* 2) fallback: any block holding table cells (skips markdown cells so IDs don't get boxed) */
    div:has(.td-id):not(:has(iframe)):not(div[data-testid="stMarkdownContainer"] *){
      background:#FFFFFF !important;
    }
    /* 3) NEW: uniform vertical margins for centered cells (only addition) */
    .td, .td-id, .td-summary, .td-next { margin: 0; line-height: 1.5; }
    div[data-testid="stHorizontalBlock"]:has(.td-id) { padding: .65rem 0; }
    hr.row-line { margin: .15rem 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='margin:.5rem 0 .8rem 0'>💼 Job Dashboard</h2>",
                unsafe_allow_html=True)
    st.markdown(
        "<div style='background:#F5F9FF;border:1px solid #D8E6F7;border-radius:14px;"
        "padding:.9rem 1.2rem;margin:0 0 1.1rem 0;"
        "font-size:.85rem;color:#44566C;line-height:1.6'>"
        "<b style='color:#16324F'>How this demo works:</b> imagine a job-related email lands in your inbox. "
        "This app securely connects to a sandbox inbox (Mailtrap) and runs every mail through an end-to-end AI pipeline:"
        "<div style='margin:.6rem 0 .55rem 0;display:flex;flex-wrap:wrap;gap:.35rem;align-items:center'>"
        "<span style='background:#FFFFFF;border:1px solid #BFDBFE;color:#2563EB;padding:.22rem .65rem;border-radius:999px;font-weight:600'>📥 Mail received</span>"
        "<span style='color:#94A3B8'>→</span>"
        "<span style='background:#FFFFFF;border:1px solid #BFDBFE;color:#2563EB;padding:.22rem .65rem;border-radius:999px;font-weight:600'>🔌 Fetched via POP3</span>"
        "<span style='color:#94A3B8'>→</span>"
        "<span style='background:#FFFFFF;border:1px solid #BFDBFE;color:#2563EB;padding:.22rem .65rem;border-radius:999px;font-weight:600'>🤖 Gemini reads &amp; classifies as </span>"
        "<span style='color:#94A3B8'>→</span>"
        "<span style='background:#FFFFFF;border:1px solid #BFDBFE;color:#2563EB;padding:.22rem .65rem;border-radius:999px;font-weight:600'>💼 Applied Job vs Offer-without-application</span>"
        "<span style='color:#94A3B8'>→</span>"
        "<span style='background:#FFFFFF;border:1px solid #BFDBFE;color:#2563EB;padding:.22rem .65rem;border-radius:999px;font-weight:600'>📊 Updates the Job Offer in Dashboard + Suggests subsequent action</span>"
        "</div>"
        "An <b>AI Based recommendation system</b> further ranks your live opportunities and suggests which offer deserves your acceptance first.<br>"
        "<b>Want to try it live?</b> Jump to <b>🧪 Test by sending an email</b> at the bottom of this page — "
        "the sandbox inbox is pre-connected, so send a sample mail, press <b>🔄 Sync now</b>, "
        "and watch it flow through the pipeline into the tables above within seconds. "
        "No real mailbox is ever touched."
        "</div>",
        unsafe_allow_html=True)
    
    ok = STATUS["last_err"] is None

    ok = STATUS["last_err"] is None
    chip_class = "chip-ok" if ok else "chip-err"
    if ok:
        chip_text = "🟢 Sync healthy · last success " + (STATUS["last_ok"] or "")
    else:
        chip_text = "🔴 " + str(STATUS["last_err"])
    st.markdown(f"<span class='chip {chip_class}'>{chip_text}</span>",
                unsafe_allow_html=True)

    BUILD = "v0823a"   # bump this tag on EVERY push so we can verify the cloud is fresh
    rep = STATUS.get("report")
    line = f"[{BUILD}] scanning since {get_scan_since().strftime('%Y-%m-%d %H:%M')}"
    if rep:
        line += (f" · fetched {rep['fetched']} · duplicates skipped {rep['dup']}"
                 f" · not job-related {rep['not_job']} · added {rep['added']}"
                 f" · retry {rep.get('retry', 0)} · rescued {rep.get('reclassified', 0)}")
        if rep.get("cls_err"):
            line += f" · ⚠️ CLS ERROR: {rep['cls_err']}"
    st.caption(line)


    jobs = get_jobs()
    # Inject message_id into display dict so we don't lose it during collapse
    raw_dicts = []
    for mid, j in jobs.items():
        d = _disp(j)
        d["_mid"] = mid
        raw_dicts.append(d)
        
    collapsed_dicts = collapse_duplicates(raw_dicts, threshold=2)
    pairs = [(d["_mid"], d) for d in collapsed_dicts]
    visible = [(mid, d) for mid, d in pairs if d.get("category") in ("applied", "cold_offer")]
    applied = [(mid, d) for mid, d in visible if d["category"] == "applied"]
    cold = [(mid, d) for mid, d in visible if d["category"] == "cold_offer"]

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        _kpi("📝", "Applied Jobs", len(applied), BLUE)
    with k2:
        _kpi("🎯", "Cold Offers", len(cold), AMBER)
    with k3:
        _kpi("💼", "Total Opportunities", len(visible), "#22D3EE")

    _spacer("1.75rem")

    ch1, ch2 = st.columns(2, gap="large")
    with ch1:
        with st.container(border=True):
            _chart_header("Count of Jobs applied by you vs Cold Offers",
                          "Share of jobs you applied to vs Jobs offered by the recruiters without prior application.")
            st.plotly_chart(_donut(len(applied), len(cold)),
                            width="stretch",
                            config={"displayModeBar": False, "displaylogo": False})
    with ch2:
        with st.container(border=True):
            _chart_header("Count of Jobs received since Last 10days",
                          "Count of job-related emails received over the last 10 days.")
            st.plotly_chart(_timeline(visible),
                            width="stretch",
                            config={"displayModeBar": False, "displaylogo": False})

    with st.expander("🩺 API diagnostics (cloud debugging)"):
        st.caption("Makes one tiny generate call + one embedding call and shows the EXACT "
                   "status code and message Google returns.")
        if st.button("Run diagnostic", key="run_diag"):
            import os as _os
            from google import genai as _genai

            key = _os.getenv("GEMINI_API_KEY")
            if not key:
                try:
                    key = st.secrets["GEMINI_API_KEY"]
                except Exception:
                    key = None
            st.write(f"Key loaded: {'✅' if key else '❌'} · length {len(key or '')} "
                     f"· starts with '{(key or '')[:4]}…'")

            if key:
                c = _genai.Client(api_key=key)
                try:
                    r = c.models.generate_content(
                        model="gemini-3.1-flash-lite", contents="Reply with the word pong")
                    st.success(f"✅ Generate OK → {r.text[:40]}")
                except Exception as e:
                    st.error(f"❌ generate: {type(e).__name__} · HTTP {getattr(e, 'code', '?')} · {str(e)[:500]}")
                try:
                    c.models.embed_content(model="text-embedding-004", contents="ping")
                    st.success("✅ Embeddings OK")
                except Exception as e:
                    st.error(f"❌ embed: {type(e).__name__} · HTTP {getattr(e, 'code', '?')} · {str(e)[:500]}")

    _table_section("Applied Jobs", "📝", applied, "applied", BLUE)
    _table_section("Job Offers without prior application", "🎯", cold, "cold", AMBER)
       
    _recommendation_section()
    _spacer("2rem")

    # Feedback shown OUTSIDE the dropdown so it's visible even when collapsed
        # Feedback shown OUTSIDE the dropdown so it's visible even when collapsed
    tmsg = st.session_state.get("test_msg")
    if tmsg:
        if tmsg.startswith("✅"):
            st.success(tmsg)
            # One-click sync right next to the banner — no expander hunting
            if st.button("🔄 Sync now", key="sync_after_send", width="stretch"):
                st.session_state.pop("test_msg", None)
                sync_now()
                st.rerun()
        elif tmsg.startswith("❌"):
            st.error(tmsg)
        else:
            st.warning(tmsg)

    # Stays OPEN while a test message is pending; collapsed otherwise
    with st.expander("🧪 Test by sending an email", expanded=bool(tmsg)):

        st.caption("Type or paste any email text and send it into the sandbox. "
                   "The AI decides whether it's an application response or a cold offer.")
        frm = st.text_input("From (optional)", value="Recruiter <recruiter@company.com>")
        subj = st.text_input("Subject (optional)", value="New opportunity")
        body = st.text_area("Email body — type / paste your custom text", height=150)
        b1, b2 = st.columns(2)
        if b1.button("📨 Send email", width="stretch"):
            if body.strip():
                try:
                    send_test_email(subj, frm, body)
                    st.session_state["test_msg"] = "✅ Successfully sent the mail! Press 🔄 Sync Now."
                except Exception as e:
                    st.session_state["test_msg"] = f"❌ {e}"
            else:
                st.session_state["test_msg"] = "Write some email text first."
            st.rerun()
        if b2.button("🔄 Sync now", width="stretch"):
            st.session_state.pop("test_msg", None)
            sync_now()
            st.rerun()