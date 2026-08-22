import streamlit as st

st.set_page_config(page_title="AI Job Platform", page_icon="💼", layout="wide")

# Font loaded via <link> AND @import (belt & braces)
st.markdown(
'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
'family=Geist:wght@100..900&family=Geist+Mono:wght@100..900&display=swap">',
unsafe_allow_html=True)

st.markdown("""
<style>
/* --- kill top whitespace --- */
header[data-testid="stHeader"] { display: none !important; }
div.block-container { padding-top: 1rem !important; }

# @import url('https://fonts.googleapis.com/css2?family=Geist:wght@100..900&family=Geist+Mono:wght@100..900&display=swap');

# /* +4pt global bump */
# html { font-size: 20px; }

# /* Geist on all text content (narrow selector — doesn't break widget internals) */
# body, p, h1, h2, h3, h4, h5, button, input, textarea, label,
# div[data-testid="stMarkdownContainer"], div[data-testid="stMarkdownContainer"] span,
# div[data-testid="stMarkdownContainer"] div, div[data-testid="stMetric"] {
#   font-family: 'Geist', -apple-system, 'Segoe UI', sans-serif !important;
# }
# .mono, .mono * { font-family: 'Geist Mono', monospace !important; }

# /* clean chrome + no top gap */
# #MainMenu, footer { visibility: hidden; }
# header[data-testid="stHeader"] { display: none; }
# div[data-testid="stAppViewContainer"] section.main div.block-container { padding-top: 0rem; }
# .stApp { background: #F5F7FB; }
# div[data-testid="stSidebar"] { display: none; }

# /* gradient header */
# .site-head{
#   background: linear-gradient(135deg, #16324F 0%, #1F4E79 55%, #2E6DB4 100%);
#   border-radius:16px; padding:1.1rem 1.6rem; min-height:10vh;
#   display:flex; align-items:center; justify-content:space-between;
#   box-shadow:0 6px 18px rgba(22,50,79,.25); margin-bottom:1rem;
# }
# .site-head h1{ color:#fff; margin:0; font-size:1.55rem; font-weight:800; text-align:left; }
# .site-head p{ color:#BBD3EA; margin:2px 0 0 0; font-size:.9rem; text-align:left; }

# .stButton > button { border-radius:10px; height:2.9rem; font-weight:600; }

# .kpi{ background:#fff; border-radius:14px; padding:.95rem 1.2rem;
#   border:1px solid #E3EAF3; box-shadow:0 2px 8px rgba(16,50,80,.06); }
# .kpi-label{ color:#68788C; font-size:.72rem; text-transform:uppercase;
#   letter-spacing:.07em; font-weight:700; }
# .kpi-value{ font-size:1.9rem; font-weight:800; color:#16324F; margin-top:.15rem; }

# .chip{ display:inline-block; padding:.3rem .85rem; border-radius:999px;
#   font-size:.78rem; font-weight:700; }
# .chip-ok{ background:#E6F6EC; color:#1B7F3B; border:1px solid #BFE6CC; }
# .chip-err{ background:#FDECEC; color:#B33535; border:1px solid #F5C6C6; }

# .pill{ display:inline-block; padding:.18rem .65rem; border-radius:999px;
#   font-size:.75rem; font-weight:800; margin-left:.5rem; vertical-align:middle; }

# div[data-testid="stVerticalBlockBorderWrapper"]{
#   background:#fff; border:1px solid #E3EAF3 !important; border-radius:16px !important;
#   box-shadow:0 1px 4px rgba(16,50,80,.05); transition:box-shadow .2s ease; margin-top:5px; margin-bottom:5px;
# }
# div[data-testid="stVerticalBlockBorderWrapper"]:hover{ box-shadow:0 6px 16px rgba(16,50,80,.12); }

# /* ---- professional table styling ---- */
# .th{ color:#68788C; font-size:.68rem; text-transform:uppercase;
#      letter-spacing:.08em; font-weight:700; padding:.1rem 0 .55rem 0; }
# .td{ font-size:.86rem; color:#22303F; font-weight:500; }
# .td-id{ font-family:'Geist Mono',monospace; font-weight:700;
#         color:#16324F; font-size:.8rem; letter-spacing:.02em; }
# .td-date{ font-family:'Geist Mono',monospace; color:#68788C; font-size:.78rem; }
# .td-summary{ font-size:.82rem; color:#44566C; line-height:1.5; }
# hr.row-line{ border:none; border-top:1px solid #EDF1F7; margin:.7rem 0 !important; }

@import url('https://fonts.googleapis.com/css2?family=Geist:wght@100..900&family=Geist+Mono:wght@100..900&display=swap');

html { font-size: 20px; }

body, p, h1, h2, h3, h4, h5, button, input, textarea, label,
div[data-testid="stMarkdownContainer"], div[data-testid="stMarkdownContainer"] span,
div[data-testid="stMarkdownContainer"] div, div[data-testid="stMetric"] {
  font-family: 'Geist', -apple-system, 'Segoe UI', sans-serif !important;
}
.mono, .mono * { font-family: 'Geist Mono', monospace !important; }

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
div.block-container { padding-top: 1rem !important; }
div[data-testid="stSidebar"] { display: none; }

/* ---------- light background with soft color washes ---------- */
.stApp {
  background:
    radial-gradient(900px 480px at 90% -10%, rgba(37,99,235,.07), transparent 60%),
    radial-gradient(800px 420px at -10% 20%, rgba(8,145,178,.06), transparent 60%),
    radial-gradient(700px 420px at 50% 110%, rgba(245,158,11,.05), transparent 60%),
    #F4F7FC;
}

/* ---------- crisp white cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF !important;
  border: 1px solid #E3EAF3 !important;
  border-radius: 16px !important;
  box-shadow: 0 2px 10px rgba(16,50,80,.06);
  transition: box-shadow .2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: 0 6px 16px rgba(16,50,80,.12);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.td-id){
  background:#FFFFFF !important;
  border:1px solid #E3EAF3 !important;
  border-radius:16px !important;
}

/* ---------- header: white card + thick gradient heading ---------- */
.site-head {
  background: #fff;
  border: 1px solid #E3EAF3; border-left: 6px solid #2563EB;
  border-radius: 16px; padding: 1.1rem 1.6rem; min-height: 10vh;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 4px 16px rgba(16,50,80,.08);
  margin-bottom: 1rem;
}
.site-head h1 {
  margin: 0; font-size: 1.55rem; font-weight: 800;
  background: linear-gradient(90deg, #16324F, #2563EB 55%, #0891B2);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.site-head p { color: #5A6B80; margin: 2px 0 0 0; font-size: .9rem; }

/* ---------- bold buttons ---------- */
.stButton > button {
  border-radius: 12px; height: 2.9rem; font-weight: 700;
  background: #fff; color: #2563EB;
  border: 2px solid #2563EB;
  transition: all .2s ease;
}
.stButton > button:hover {
  background: #2563EB; color: #fff;
  box-shadow: 0 6px 18px rgba(37,99,235,.30);
}
button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #2563EB, #0891B2) !important;
  border: none !important; color: #fff !important;
  box-shadow: 0 6px 18px rgba(37,99,235,.35);
}
button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); }

/* ---------- KPI cards (numbers get thick accent colors from code) ---------- */
.kpi {
  background: #fff; border: 1px solid #E3EAF3; border-radius: 16px;
  padding: .95rem 1.2rem;
  box-shadow: 0 2px 10px rgba(16,50,80,.06);
}
.kpi-label { color: #68788C; font-size: .72rem; text-transform: uppercase;
  letter-spacing: .08em; font-weight: 700; }
.kpi-value { font-size: 1.9rem; font-weight: 800; margin-top: .15rem; }

/* ---------- chips & pills ---------- */
.chip { display: inline-block; padding: .3rem .85rem; border-radius: 999px;
  font-size: .78rem; font-weight: 700; }
.chip-ok { background: #E6F6EC; color: #1B7F3B; border: 1px solid #BFE6CC; }
.chip-err { background: #FDECEC; color: #B33535; border: 1px solid #F5C6C6; }
.pill { display: inline-block; padding: .18rem .65rem; border-radius: 999px;
  font-size: .75rem; font-weight: 800; margin-left: .5rem; vertical-align: middle; }

/* ---------- inputs ---------- */
div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[role="combobox"] {
  background: #fff !important; border: 1.5px solid #D5E0EE !important;
  color: #22303F !important; border-radius: 10px;
}
input:focus, textarea:focus {
  border-color: #2563EB !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,.15) !important;
}

/* ---------- headings ---------- */
h3 { color: #16324F; font-weight: 800; }

/* ---------- tables ---------- */
.th { color: #68788C; font-size: .68rem; text-transform: uppercase;
  letter-spacing: .08em; font-weight: 700; padding: .1rem 0 .55rem 0; }
.td { font-size: .86rem; color: #22303F; font-weight: 500; }
.td-id { font-family: 'Geist Mono', monospace; font-weight: 700;
  color: #2563EB; font-size: .8rem; letter-spacing: .02em; }
.td-date { font-family: 'Geist Mono', monospace; color: #68788C; font-size: .78rem; }
.td-summary { font-size: .82rem; color: #44566C; line-height: 1.5; }
hr.row-line { border: none; border-top: 1px solid #EDF1F7; margin: .7rem 0 !important; }

/* ---- Next Step column: bold action color ---- */
.td-next { font-size: .82rem; font-weight: 700; color: #EA580C; line-height: 1.4; }

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="site-head">
  <div>
    <h1>💼 AI Job Application Platform</h1>
    <p>Track every application & opportunity — powered by AI</p>
  </div>
</div>
""", unsafe_allow_html=True)

# --- page routing that survives refreshes / reconnects / long AI calls ---
_qp = st.query_params.get("page")
if _qp in ("dashboard", "tailor", "eval"):
    st.session_state.page = _qp
elif "page" not in st.session_state:
    st.session_state.page = "dashboard"

n1, n2, n3 = st.columns(3, gap="small")
if n1.button("📊 Job Dashboard", width="stretch",
             type="primary" if st.session_state.page == "dashboard" else "secondary"):
    st.session_state.page = "dashboard"
    st.query_params["page"] = "dashboard"
    st.rerun()
if n2.button("📄 Resume Designer", width="stretch",
             type="primary" if st.session_state.page == "tailor" else "secondary"):
    st.session_state.page = "tailor"
    st.query_params["page"] = "tailor"
    st.rerun()
if n3.button("🧪 RAG Eval", width="stretch",
             type="primary" if st.session_state.page == "eval" else "secondary"):
    st.session_state.page = "eval"
    st.query_params["page"] = "eval"
    st.rerun()

st.write("")

if st.session_state.page == "dashboard":
    from views.dashboard_view import render
    render()
elif st.session_state.page == "tailor":
    from views.tailor_view import render
    render()
else:
    from views.eval_view import render
    render()
  
