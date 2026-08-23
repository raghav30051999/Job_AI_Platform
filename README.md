# 🤖 AI Job Platform

An end-to-end AI copilot for job seekers — it monitors a sandbox email inbox, where companies typically send automated emails after receiving a job application or extending a job offer. A Gemini AI model continuously analyzes these emails, classifies job opportunities, and ranks them based on their importance, making it easier to track and manage job offers seamlessly.

To address the other side of the job-search process i.e. applying for jobs — our project includes a 'Resume Designer' section. The user's profile is converted into embeddings and stored for retrieval. Using a RAG-based retrieval pipeline, the system retrieves relevant information from the profile and validates it against the requirements of a given job description. Based on this validation, it generates a tailored, ATS-friendly resume with grounded, citation-backed content, ensuring that the resume is both relevant to the role and supported by the user's actual profile.

The RAG pipeline is also evaluated to measure the quality and reliability of retrieval and generated responses.

🔗 **Wanna try this ? Click here :** [https://jobaiplatform-rtrignv3fkd8tqzdzs9yxw.streamlit.app/]

---

## 📖 Overview

The platform closes the loop between *hearing about jobs* and *applying well*:

1. **Job Dashboard** — emails flow in from a Mailtrap sandbox inbox over POP3; a Gemini classifier extracts company, role etc and suggests next step.
Duplicate mails are also being handled with entity-resolution.
Among the received Job Offers, an AI based recommendation system ranks best and personalized opportunities which suits your profile.
2. **Resume Designer** — your profile is chunked, embedded, and indexed; for any JD, hybrid RAG retrieves the right evidence and a two-pass Gemini pipeline (writer + ruthless editor with frozen facts) produces a submit-ready resume in `.docx / .pdf / .txt`.
3. **RAG Eval Lab** — the evaluation metrics of RAG pipeline can be assessed at 'RAG Eval' section: recall, faithfulness, citation accuracy, unsupported-claim rate, latency, and cost.

---

## ✨ Feature Highlights

### 💼 Job Dashboard
- **POP3 ingestion** with multi-strategy connection cache (SSL / STARTTLS / plain).
- **AI classification** into *Applied* vs *Cold Offer* with actionable next steps; interview invites, shortlists, offers, and rejections all recognized.
- **Two-layer deduplication**: hard (message-id + content hash + blacklist) and soft (normalized company+role entity resolution with `×N` badges).
- **Self-healing repair pass** that re-evaluates previously hidden mails whenever the classifier is upgraded (`CLS_VERSION`).
- **AI recommendation engine** — generic mode + **personalized mode** powered by profile RAG; auto-refreshes whenever the job list changes.
- **Live KPIs & charts** (Plotly): applied vs cold-offer donut, 10-day intake timeline.
- **Inline editing**, two-step delete confirmation, and bulk actions.

### 📄 Resume Designer
- **Profile indexing**: heading-aware chunking, Gemini embeddings, incremental re-indexing with vector reuse, live progress bar.
- **Hybrid retrieval**: dense cosine + BM25 sparse, fused with **Reciprocal Rank Fusion**, intent-aware section boosts, optional **LLM rerank**.
- **Grounded generation**: strict evidence-only system prompt, career-transition framing detector, and a **frozen-facts editor pass** that polishes without inventing.
- **Deterministic safety nets**: education entries are re-parsed from the raw profile so no degree/CGPA can ever be dropped; score normalization (`CGPA 8.29` / `90.2%`).
- **ATS exports**: justified, tight-spaced `.docx`, ASCII-safe `.pdf`, and plain `.txt`.

### 🧪 RAG Eval Lab
| Metric | What it measures |
|---|---|
| Retrieval Recall@k | Right profile chunks surfaced for a JD |
| Faithfulness | Resume claims supported by retrieved evidence |
| Citation Accuracy | Bullet ↔ evidence alignment |
| Unsupported-Claim Rate | Hallucination pressure of the generator |
| Latency (p50/p95) | Per-stage responsiveness |
| Cost / run | Token accounting per generation |

---

## 🏗️ Architecture
```text
PART 1 - JOB TRACKING (what the Dashboard shows)
================================================

  [1] TEST INBOX (Mailtrap sandbox)
      A safe practice mailbox, though the users can't be able to reach the sandboxed mail, however the inbox is pre-connected to the project for testing.
      |
      | a mail arrives
      v
  [2] AI MAIL READER (Gemini)
      Reads it: "Job-related? Which company? Which role? What next?"
      |
      | writes a tidy job card
      v
  [3] JOB MEMORY (saved on GitHub, survives restarts)
      Keeps every card; throws away duplicates and spam.
      |
      +-------------------------------+
      | (show it)                     | (rank it)
      v                               v
  [4] JOB DASHBOARD               [5] AI Based recommendation
      Tables + charts +           "Ranks the best 
      next-step advice            opportunity first (Personalized ranking feature is also available)"


PART 2 - RESUME DESIGNER (how your resume is built)
===================================================

  [6] YOUR PROFILE                [7] JOB DESCRIPTION
      Pasted once; chopped            The job you want;
      into pieces & memorized         pasted per application
      |                               |
      | your real experience          | what this job needs
      +---------------+---------------+
                      |
                      v
                [8] SMART SEARCH (RAG)
                    Finds ONLY the pieces of your
                    history that match this job
                      |
                      | evidence pack
                      v
                [9] AI RESUME WRITER
                    Prepares resume with those facts collected from user profile ; the editor
                    polishes words but may never change
                    a single fact
                      |
                      v
                [10] DOWNLOAD
                    Provides resume in ".docx/.pdf/.txt" format for flexible uses


  LINK BETWEEN THE PARTS
  ======================
  [6] YOUR PROFILE also powers the Dashboard's
  "Personalized mode" ranking in [5].
```

**Persistence model:** Streamlit Cloud's disk is ephemeral, so the app treats **GitHub as its database** — every sync is debounced and pushed to a non-deployed `cloud-state` branch; on boot the store is hydrated from there. Local runs fall back to plain files. Zero extra services.

---

## 🧰 Tech Stack

- **App:** Streamlit · Plotly · python-docx · fpdf2 · BeautifulSoup
- **AI:** Google Gemini (`gemini-3.1-flash-lite`) — generation, classification, rerank, embeddings
- **Mail:** Mailtrap sandbox (POP3 + SMTP)
- **Persistence:** GitHub Contents API (side-branch state) + JSON stores
- **IR:** hand-rolled BM25 + cosine + RRF (no vector DB dependency)

---

## 📁 Project Structure

```
job_ai_platform/
├── app.py                  # router, theming, URL-safe page state
├── requirements.txt
├── utils/config.py         # secrets-first config (Cloud ⇄ local .env)
├── core/
│   ├── gemini_client.py    # single client, safe init, robust JSON parsing
│   ├── email_reader.py     # POP3 fetch + connection strategy cache
│   ├── email_classifier.py # AI classification w/ retry & backoff
│   ├── job_store.py        # store, dedup, repair pass, sync report
│   ├── job_sync.py         # orchestration + status + reco auto-refresh
│   ├── cloud_persist.py    # GitHub-as-DB (cloud-state branch)
│   ├── dedup.py            # entity resolution & ×N collapse
│   ├── recommender.py      # AI copilot (generic / personalized)
│   ├── profile_rag.py      # chunking, hybrid retrieval, RRF, rerank
│   ├── embeddings.py       # Gemini embeddings w/ pacing
│   ├── resume_tailor.py    # evidence pack + grounded two-pass writer
│   ├── exporters.py        # ATS .docx / .pdf / .txt
│   └── settings.py         # scan baseline
└── views/
    ├── dashboard_view.py
    ├── tailor_view.py
    └── eval_view.py        # RAG evaluation lab
```

---

## 🚀 Run It Locally

```bash
git clone https://github.com/<you>/job_ai_platform.git
cd job_ai_platform
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

cat > .env <<EOF
GEMINI_API_KEY=...
POP3_HOST=pop3.mailtrap.io
POP3_PORT=9950
POP3_USER=...
POP3_PASS=...
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=...
SMTP_PASS=...
EOF

streamlit run app.py
```

---

## ☁️ Deploy to Streamlit Community Cloud

1. Push this repo; create the app from `app.py` on branch `main`.
2. Create a **non-deployed** branch for state: `git checkout -b cloud-state && git push -u origin cloud-state`.
3. Add **Secrets** (Settings → Secrets):

```toml
GEMINI_API_KEY = "..."
GITHUB_TOKEN   = "github_pat_..."   # fine-grained, Contents: rw, this repo only
POP3_HOST = "pop3.mailtrap.io"
POP3_PORT = "9950"
POP3_USER = "..."
POP3_PASS = "..."
SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = "587"
SMTP_USER = "..."
SMTP_PASS = "..."
```

4. Reboot. The dashboard hydrates from `cloud-state` and every sync persists back to it.

---


## Future updates

- Making the project supported for multi-user login.
- Application tracker kanban (applied → interview → offer).
- Salary package analysis and salary negotiation recommendation system.
- Trend analysis and industry-ready skills recommendation system. 


---

## 📄 License & Contact

MIT — built by **[Sri Raghavendra Puvvula]** · [raghavnaveen111@gmail.com]