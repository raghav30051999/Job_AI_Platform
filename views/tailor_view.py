import streamlit as st
from core.profile_rag import save_profile, get_profile, clear_profile, append_profile
from core.resume_tailor import tailor_for_jd, jd_hash
from core.exporters import build_docx, build_pdf, _fmt_score  

SAMPLE_PROFILE = """Sri Raghavendra Puvvula 
AI/ML Engineer | Agentic AI & Workflow Automation Specialist
Kakinada, Andhra Pradesh, India | 9912525797 | raghavnaveen111@gmail.com
Agentic AI • LLM Orchestration • RAG •  n8n • MCP • OCR & Document Intelligence • Python
PROFESSIONAL SUMMARY
Applied AI Engineer with a B.Tech in Electrical & Electronics Engineering and 5+ years of self-driven, hands-on expertise building production-grade Agentic AI and automation systems. Specializes in designing end-to-end AI workflows spanning Large Language Models, Retrieval-Augmented Generation (RAG), multi-agent orchestration (LangGraph, CrewAI), and workflow automation (n8n) to solve real-world document intelligence and business-process problems. Proven track record of taking AI systems from prototype to production in high-compliance, high-volume environments — including multilingual OCR pipelines, Model Context Protocol (MCP) tool servers, and large-scale government workflow automation. Systems-first thinker who prioritizes deployable, real-world impact over isolated model experimentation.
CORE TECHNICAL SKILLS
Agentic AI & LLM Orchestration: Hermes Agent, Multi-Agent Systems, Model Context Protocol (MCP), Tool Calling, Autonomous Planning & Reasoning Systems.
Retrieval-Augmented Generation (RAG) & Knowledge Systems: RAG Pipeline Design, Vector Databases, Embedding Pipelines, Document Chunking.
Workflow & Business Process Automation: n8n, REST API Automation, Web Data Extraction, Business Process Automation.
Document Intelligence & OCR: OCR Pipeline Engineering (Docker-hosted), PDF Processing, Structured Data Extraction, Multilingual (Telugu-English) Document Processing, Legal & Government Document Digitization.
Programming: Python, HTML, CSS, Git/GitHub.
Data Science & Machine Learning: Pandas, NumPy, Statistical Analysis, Exploratory Data Analysis.
Infrastructure & Databases: Docker, Vector Database.
AI Ecosystem & Local Deployment: Ollama, AnythingLLM, Google Gemini, Google AI Studio, Open-Source LLM Deployment, Quantized Models.
PROFESSIONAL EXPERIENCE (NON-IT)
Junior Assistant	July, 2021 – Present
Government of Andhra Pradesh — Municipal Administration Department.
•	Designed automation workflow for tracking the bills uploaded in AP CFMS (Comprehensive Financial Management System).
•	Engineered a n8n-based OCR digitization pipeline that converts scanned documents or PDFs into searchable, structured text. 
•	Built a RAG Pipeline embeds and stores the data into vector database, automatically generation the correspondence and reports. 
•	Automation of CRON/Scheduled, repetitive Jobs using Agentic AI and eliminated the human intervention for repetitive tasks. 
•	Analysis, Processing, and Generation of Legal Documentation using Agentic AI Solutions.
•	Built an app that automatically generates the Government Correspondences by pulling the real time data from the Sources like Google Sheets, Google Drive etc.
SELECTED INDEPENDENT PROJECTS
Fraud Insurance Claim Prediction – Designed and developed a Machine Learning model to predict the fraud Vehicle Insurance Claim using Machine Learning Algorithms viz Linear Regression, Decision Trees, Random Forest, XGBoost etc. 
Multilingual Legal-Document OCR Pipeline — Designed a fully local, privacy-preserving n8n workflow integrating a Dockerized OCR API to extract text from scanned PDFs and parsing structured output data, engineered under strict offline/architectural constraints to keep sensitive data on-premises.
Local Agentic AI Assistant (Hermes) — Custom Memory & Reasoning Architecture — Configured a self-hosted agent that implements a 7-phase deliberate reasoning cycle (Observe, Analyze, Hypothesize, Evaluate, Decide, Act, Reflect) to improve the consistency and quality of autonomous agent decisions.
Configured the memory for exceptional accuracy in repetitive tasks. 
Automated Generation of Government Correspondence and Reports  — Built a robust system that embeds the data and stores it in Vector Database for autonomous generation of accurate & well structured Government correspondence like letters, orders, etc., and MCP integration to turn the structured data into word, PDF, PPT or excel, which aids instant decision  making.
Local Models – Integration of Model Context Protocol (MCP) and Local AI Models for repititive task automation, ensuring high productivity and robust data privacy.
EDUCATION
B.Tech, Electrical & Electronics Engineering	2016-2020
Pragati Engineering College, Surampalem, Andhra Pradesh
CGPA – 8.29
Intermediate (MPC)	2014-2016
Aditya Junior College, Kakinada, Andhra Pradesh
Percentage –90.2
SSC	2013-2014
Sri Vivekananda Talent School, Samalkot, Andhra Pradesh
CGPA – 9.2
ADDITIONAL INFORMATION
Languages: English (Professional Working Proficiency), Telugu (Native), Hindi


# AI/ML & Software Engineering Skill Profile

## 1. Professional Profile

**Current background:** Government-sector administrative/technical professional transitioning into **AI/ML, Data Science, Generative AI, Agentic AI, and Software Engineering**.

**Primary career objective:** Move from a non-IT government role into an **AI/ML Engineer / Applied AI / GenAI / Agentic AI / ML Engineer** position by demonstrating practical engineering ability through projects, deployment, automation, and problem-solving.

**Career positioning:**
- Non-traditional/fresher transitioner into IT.
- Strong interest in **practical AI systems rather than purely theoretical ML**.
- Particularly interested in combining **ML + LLMs + agents + automation + software engineering**.
- Strong preference for projects that resemble real production problems and demonstrate end-to-end ownership.

---

# 2. Core Technical Interest Areas

### Primary Areas

1. **Agentic AI / Autonomous AI Systems**
2. **Generative AI / LLM Applications**
3. **Machine Learning**
4. **Data Science**
5. **AI-powered Automation**
6. **Software Engineering / Full-Stack Integration**
7. **AI-assisted Research Systems**
8. **Financial/Trading AI**

### Interest Priority

**Agentic AI & Automation > Machine Learning > Data Science**

The user's strongest long-term interest is building systems that can **reason, use tools, retrieve information, make decisions, and execute multi-step workflows automatically**.

---

# 3. Machine Learning Skills

## Supervised Learning

Demonstrated understanding and practical experimentation with:

- Logistic Regression
- Random Forest
- XGBoost
- Balanced Random Forest
- Decision Trees
- K-Nearest Neighbors
- Perceptron
- Classification problems
- Binary classification
- Model comparison
- Threshold optimization

## Model Evaluation

Understands and actively works with:

- Precision
- Recall
- F1-score
- Confusion Matrix
- False Positives
- False Negatives
- Imbalanced classification
- Stratified train/test splitting
- Unseen test data
- Model threshold optimization

The user does not merely memorize metrics; they repeatedly reason about **what the metrics mean operationally**, especially the relationship among precision, recall, false positives, and false negatives.

---

# 4. Imbalanced Learning

Strong practical interest and understanding of imbalanced classification techniques.

Concepts studied:

- Class imbalance
- SMOTE
- Synthetic minority sampling
- Training-only resampling
- Data leakage caused by preprocessing before train/test separation
- Relationship between resampling and model evaluation
- BalancedRandomForestClassifier

The user specifically investigated **why SMOTE must be applied only to training data** and how applying it before splitting can contaminate evaluation data.

---

# 5. Major Machine Learning Project

## Vehicle Insurance Fraud Detection

A substantial ML classification project based on the **Angoss/Kaggle vehicle insurance claims fraud dataset**.

### Dataset

- Approximately **15,420 records**
- One corrupted record removed
- Highly imbalanced fraud classification problem
- Approximately **6% fraudulent claims**
- Historical data spanning **1994–1996**

### Models Evaluated

- Logistic Regression
- Random Forest
- XGBoost
- Balanced Random Forest

### Final Model

**BalancedRandomForestClassifier**

### Evaluation

- Stratified **80/20 train-test split**
- Fraud ratio preserved between training and testing
- Optimized prediction threshold
- Final reported test **F1-score ≈ 0.27**

### Important Modeling Decisions

- Dataset imbalance explicitly considered.
- Target distribution preserved through stratification.
- Threshold optimization used rather than blindly using the default 0.5 threshold.
- Test set treated as unseen evaluation data.
- The user explicitly investigated **data leakage**, particularly around resampling.
- The `Year` feature was excluded to reduce dependence on the historical period.
- Recognizes that the evaluation methodology matters as much as the model choice.

### Demonstrated Skills

This project demonstrates:

- End-to-end classification workflow
- Data preprocessing
- Feature/target handling
- Imbalanced-learning strategies
- Multiple-model experimentation
- Evaluation strategy
- Threshold optimization
- Leakage awareness
- Model selection based on problem characteristics

---

# 6. Data Science Skills

Practical experience/interests include:

- Python
- pandas
- NumPy
- Matplotlib
- Seaborn
- Dataset inspection
- Feature analysis
- Data cleaning
- Null-value handling
- KNN imputation
- Exploratory analysis
- Classification datasets
- Statistical concepts
- Entropy
- Decision-tree mathematics
- Hypothesis testing
- Feature-target relationships
- Visualization
- Model evaluation

The user frequently asks **why an algorithm works**, not merely how to execute it.

Examples of concepts explored:

- Entropy in Decision Trees
- KNN Imputation
- Hypothesis testing
- Precision vs Recall
- SMOTE
- Bootstrapping vs synthetic sampling
- Data leakage
- Train/test methodology

This indicates a learning style oriented toward **conceptual understanding + implementation**.

---

# 7. Generative AI / LLM Skills

The user has hands-on exposure to the LLM ecosystem.

### Models / Platforms Explored

- Ollama
- GPT4All
- Llama-family models
- Qwen
- DeepSeek
- Gemma
- Hugging Face
- Google AI Studio
- Gemini
- Claude

### Local LLM Experience

Has experimented with running models locally and understanding:

- Quantized models
- Q4_K_M quantization
- Model size vs hardware requirements
- VRAM limitations
- CPU/GPU inference
- Local model deployment
- Ollama model management
- LLM configuration

### Models Mentioned/Experimented With

- Qwen3 4B
- Qwen3.5 4B
- Qwen3-VL 8B
- Qwen2.5-Coder 7B
- DeepSeek-R1
- DeepSeek-Coder
- Gemma-family models

---

# 8. RAG / Knowledge Systems

Strong interest in building **private knowledge-based AI systems**.

Technologies/concepts explored:

- RAG
- Embeddings
- Vector databases
- Chroma
- Document ingestion
- Document indexing
- Semantic retrieval
- Local knowledge bases
- LLM grounding
- Knowledge retrieval

### AnythingLLM Experience

Hands-on experimentation with:

- Workspace creation
- PDF ingestion
- Embedding documents
- Large document collections
- Local knowledge bases
- Connecting local models to document repositories
- Diagnosing why an LLM may answer from general knowledge instead of retrieved documents

Example document corpus discussed:

- Hundreds of PDFs
- Hundreds of Excel files
- Potentially thousands of files

This indicates interest in building **enterprise-scale document intelligence systems** rather than simple chatbot demonstrations.

---

# 9. Agentic AI

This is the user's strongest AI specialization interest.

The user conceptualizes agentic systems as systems capable of:

- Dynamic decision-making
- Multi-step execution
- Tool usage
- Reasoning
- Retrieval
- Conditional branching
- Autonomous task completion
- Interaction with external systems

### Agent Framework Concepts Explored

- LangChain
- LangGraph
- Tool calling
- Autonomous workflows
- Dynamic workflows
- Agent memory
- Knowledge files
- Local agents
- MCP

The user understands the conceptual distinction between:

**LangChain → primarily composable workflows/components**

and

**LangGraph → stateful, conditional, dynamically branching agent workflows**

---

# 10. Hermes Agent / Local Agent Architecture

The user has experimented with **Hermes** as an autonomous local AI agent.

Areas explored:

- Agent configuration
- `config.yaml`
- `.env`
- `SOUL.md`
- `memory.md`
- `knowledge.md`
- Knowledge indexing
- Local model selection
- Ollama integration
- Model availability/debugging
- Agent access to local files
- Local terminal execution
- MCP integration
- Screen/keyboard/mouse automation concepts

The user is particularly interested in making AI agents capable of **operating a local computer rather than merely returning text**.

---

# 11. MCP / Tool-Using AI

Strong interest in Model Context Protocol and AI-tool integration.

Potential use cases investigated:

- Local file access
- Screen interaction
- Keyboard/mouse control
- Connecting agents to software tools
- Local-only MCP architecture
- Increasing agent capabilities through external tools

The user understands that a useful autonomous AI system requires more than an LLM; it requires **tools, memory, retrieval, execution, and environmental access**.

---

# 12. OCR / Intelligent Document Processing

One of the strongest practical automation areas.

The user has built/worked on an OCR pipeline involving:

- PDF extraction
- Selectable-text detection
- OCR fallback
- Tesseract
- Telugu + English OCR
- PDF rendering
- Image extraction
- Text extraction
- Structured output generation
- CSV/JSON/Excel conversion

### Technologies Used

- PyMuPDF
- pdfplumber
- pdfminer.six
- pytesseract
- Pillow
- pandas
- openpyxl
- NumPy
- tqdm

### Automation Architecture

Experimented with an architecture involving:

**n8n → Docker → Python worker → PDF processing → OCR → structured data**

The user also explored logic for detecting:

- Empty extracted text
- Corrupted text
- When OCR should automatically be triggered

This demonstrates practical understanding of **fallback pipelines and document-processing automation**.

---

# 13. n8n Automation

Hands-on experience with n8n workflows.

Concepts worked with:

- Workflow orchestration
- File-system automation
- HTTP requests
- Execute Command
- Google Sheets
- Batch processing
- Split-in-batches
- Docker integration
- Python workers
- OAuth troubleshooting
- Environment/configuration issues

### Intended Automation Scale

The user has discussed processing:

- Hundreds of PDFs
- Hundreds of Excel files
- Thousands of documents
- Large-volume receipts and records

This indicates interest in **automation at operational scale**, not only prototype workflows.

---

# 14. Intelligent Automation Projects / Ideas

The user frequently identifies repetitive real-world workflows that can be automated.

Examples include:

### Receipt Processing
Automate verification of thousands of receipts.

### Bill Verification
Automatically check thousands of bills and their status.

### Court Case Monitoring
Automate checking the status of thousands of court cases.

### Government Document Processing
Automatically extract structured data from government PDFs and documents.

### Municipal Receipt Scraping
Automate:

1. Login
2. Search records
3. Download PDFs
4. Extract/OCR data
5. Process records
6. Store structured information

This shows strong **business-process automation thinking**.

---

# 15. Web Scraping / API Integration

Experience with API-driven automation and scraping.

Examples:

- AP government systems
- SAP OData endpoints
- APCFSS systems
- ERP/LAMS systems
- Financial APIs
- Stock-market APIs

Technical areas investigated:

- Query filters
- OData URLs
- JSON/XML responses
- API parameters
- Error handling
- SSL/TLS issues
- HTTP errors
- Data extraction
- Converting API output into structured datasets

---

# 16. Financial/Trading Technology

The user has a strong interest in applying AI/ML to financial markets.

### Stockwatch Project

Built a stock-market web application involving:

- TwelveData API
- Python
- SQLite
- Dynamic stock search
- Company profile information
- Real-time price data
- Plotly
- Candlestick charts

### Future Trading-AI Direction

Interested in building an AI trading system involving:

- NSE/BSE
- Upstox API
- Technical analysis
- Trading books/PDF ingestion
- RAG
- AI agents
- Stock analysis
- Signal generation
- Success-rate analysis
- Profitability analysis
- Alerts before considering live execution

This combines several of the user's strongest interests:

**LLMs + RAG + Agents + APIs + ML + Automation + Finance**

---

# 17. Software Engineering Skills

### Programming

- Python
- JavaScript
- HTML
- CSS
- C

### Backend / Web

Experience or planned work with:

- Flask
- Gunicorn
- Node.js
- Express.js
- REST/API integration
- SQLite
- MySQL
- MariaDB

### Frontend

Experience/interests include:

- HTML
- CSS
- JavaScript
- React.js

### Version Control

- Git
- GitHub

### Deployment

Hands-on exposure to:

- Render
- Streamlit Community Cloud
- Gunicorn
- Docker
- Local/cloud deployment concepts

The user understands that **deployment is part of demonstrating an ML engineering project**, rather than stopping at a Jupyter notebook.

---

# 18. Full-Stack Development Exposure

Web-development projects include:

- Stock analysis website
- eCommerce WooCommerce site
- Tribute page
- Blog writing service page
- EasyBank landing page

Technical exposure:

- HTML/CSS/JavaScript
- WordPress
- WooCommerce
- Astra
- AJAX
- Product filtering
- PHP/WordPress ecosystem
- Frontend/backend integration concepts

---

# 19. Database Skills

Experience/exposure with:

- SQLite
- MySQL
- MariaDB
- phpMyAdmin
- Structured data storage
- API-to-database pipelines

Used databases in practical applications rather than studying SQL only theoretically.

---

# 20. Deployment & Production Thinking

The user demonstrates awareness of practical deployment problems such as:

- Applications sleeping after inactivity
- Recruiter-facing demo reliability
- Cloud hosting limitations
- Gunicorn configuration
- Docker environments
- Environment variables
- OAuth
- API limits
- Model availability
- Hardware limitations

This is relevant to **ML Engineering / Applied AI**, where model development alone is insufficient.

---

# 21. Hardware / Local AI Engineering Awareness

The user's local development environment has included approximately:

- Intel i5-12400HX-class CPU
- 16 GB DDR5 RAM
- NVIDIA RTX 4050
- 6 GB VRAM
- 512 GB SSD

The user actively reasons about:

- VRAM limitations
- Quantization
- Model size
- GPU utilization
- Local vs cloud inference
- CPU vs GPU execution
- Hardware requirements for LLMs

This demonstrates practical **AI infrastructure awareness**.

---

# 22. Problem-Solving Characteristics

This is one of the strongest recurring patterns in the user's conversations.

### Debugging Orientation

The user frequently works through real technical failures involving:

- YAML parsing
- Environment configuration
- Docker containers
- Missing n8n nodes
- OAuth errors
- SSL/TLS errors
- API failures
- Model availability
- Encoding problems
- OCR corruption
- Browser automation
- Deployment issues
- Local-agent permissions

### Problem-Solving Style

The user tends to:

1. Identify a concrete failure.
2. Test possible causes.
3. Ask why the failure occurs.
4. Modify the implementation.
5. Retest.
6. Continue iteratively until the architecture works.

This is significantly more representative of **engineering problem-solving** than purely theoretical learning.

---

# 23. Browser Automation

The user has built/debugged browser automation using:

- Tampermonkey
- JavaScript userscripts
- Keyboard shortcuts
- Function-key activation
- Console debugging
- Form autofill

The user has investigated issues involving:

- Script activation
- Event listeners
- Console logging
- Keyboard combinations
- Browser restrictions

This demonstrates practical understanding of **client-side automation and debugging**.

---

# 24. Research-Agent Concept

The user has a strong interest in building an autonomous AI research platform.

Core concept:

**Continuously search the internet → identify high-confidence research → analyze papers → audit evidence → extract useful applications → generate knowledge/content.**

Potential capabilities envisioned:

- Internet research
- Research-paper discovery
- Evidence evaluation
- AI/ML literature analysis
- Automated synthesis
- Application discovery
- Video generation
- Blog generation
- Knowledge-base construction

This is a strong candidate for a flagship **Agentic AI portfolio project**.

---

# 25. AI Project Architecture Preference

The user is naturally moving toward architectures combining:

```text
User / Trigger
      ↓
Agent
      ↓
Planner / Reasoner
      ↓
Retriever / RAG
      ↓
Tools / APIs
      ↓
ML Models
      ↓
Database / Knowledge Store
      ↓
Action / Recommendation
      ↓
Monitoring / Evaluation
```

This is more aligned with **Applied AI / Agentic AI Engineering** than traditional notebook-centric Data Science.

---

# 26. Technical Learning Style

The user's questions show a strong preference for:

- Conceptual explanations
- Numerical examples
- Real-world analogies
- Understanding underlying mechanisms
- Understanding failure modes
- Comparing alternative approaches
- Understanding why a method is used
- Connecting theory to production use cases

Typical pattern:

**Concept → mechanism → example → implementation → failure mode → production consideration**

This is useful for engineering roles because the user attempts to understand system behavior rather than only copy implementation patterns.

---

# 27. Strengths

### Strongest Technical Strengths

**1. AI Automation Thinking**

Naturally identifies repetitive workflows that AI can automate.

**2. Agentic AI Orientation**

Strong interest in autonomous, tool-using, stateful AI systems.

**3. Practical ML Understanding**

Has actually built and evaluated classification models.

**4. RAG / Knowledge-System Interest**

Understands embeddings, vector databases, document ingestion, and retrieval.

**5. End-to-End Mindset**

Interested in data → model → API → database → application → deployment.

**6. Debugging Persistence**

Continues troubleshooting complex implementation issues rather than abandoning the problem after the first error.

**7. Cross-Domain Integration**

Comfortable thinking across:

- ML
- LLMs
- APIs
- Databases
- Web applications
- Automation
- OCR
- Docker
- Cloud deployment

**8. Business-Problem Orientation**

Frequently frames AI around real operational problems instead of artificial benchmark tasks.

---

# 28. Areas of Technical Depth

## Strong / Demonstrated

- Python
- ML classification
- Model evaluation
- Imbalanced learning
- Data leakage concepts
- LLM experimentation
- Local LLM deployment
- RAG concepts
- AI automation
- OCR pipelines
- n8n
- APIs
- Docker-based workflows
- Web automation
- Database integration

## Intermediate / Developing

- Deep learning
- Production ML engineering
- Advanced MLOps
- Advanced backend engineering
- React
- Node.js/Express
- Advanced SQL
- Statistical modeling
- Advanced NLP
- Computer vision

## Emerging

- Multi-agent architectures
- MCP-based agents
- Autonomous research agents
- AI trading agents
- Agent memory architectures
- LLM evaluation
- Large-scale AI infrastructure

---

# 29. Portfolio Projects to Emphasize

For an AI/ML/Applied-AI resume, the strongest projects are:

### Tier 1 — Highest Resume Value

**Vehicle Insurance Fraud Detection**
- Demonstrates genuine ML competence.
- Includes imbalance handling, model comparison, threshold optimization, and evaluation.

**AI-Powered Document Intelligence Pipeline**
- PDF extraction + OCR + NLP/LLM + structured output + automation.
- Demonstrates practical enterprise AI.

**Agentic AI Research System**
- Web research + RAG + agents + evidence evaluation + content generation.
- Strong flagship project for Agentic AI roles.

### Tier 2 — Strong Supporting Projects

**StockWatch**
- API integration + database + visualization + financial data.

**AI Trading Research/Alert Agent**
- RAG + financial APIs + agent reasoning + predictive analytics.

**Government Process Automation**
- Large-scale document/receipt/bill/case-status automation.

---

# 30. Recommended Resume Positioning

The profile should **not** be presented primarily as:

> "Aspiring Data Scientist"

A stronger positioning is:

> **AI/ML Engineer | Generative AI | Agentic AI | Automation**

Alternative:

> **Applied AI / ML Engineer specializing in LLM applications, RAG, AI agents, automation, and machine learning.**

A secondary positioning can be:

> **Machine Learning Engineer with hands-on experience in fraud detection, document intelligence, LLM applications, RAG, automation, APIs, and deployment.**

---

# 31. Ideal Role Targets

Best-fit roles based on demonstrated interests and project direction:

1. **AI/ML Engineer**
2. **Applied AI Engineer**
3. **Generative AI Engineer**
4. **Agentic AI Engineer**
5. **LLM Engineer**
6. **Machine Learning Engineer**
7. **AI Automation Engineer**
8. **AI Solutions Engineer**
9. **Junior ML Engineer**
10. **AI/ML Software Engineer**

Less aligned as primary targets:

- Pure Data Analyst
- Pure BI Developer
- Pure Frontend Developer
- Pure Manual QA
- Pure Backend Developer

The strongest differentiation is the intersection:

**ML + LLM + Agents + Automation + Software Engineering**

---

# 32. Recruiter-Facing Differentiators

The user's resume should emphasize these differentiators:

### Differentiator 1
**Builds AI systems, not just ML notebooks.**

### Differentiator 2
**Combines classical ML with modern LLM/Agentic AI technologies.**

### Differentiator 3
**Has practical experience solving messy real-world automation problems.**

### Differentiator 4
**Understands data leakage, model evaluation, class imbalance, and deployment considerations.**

### Differentiator 5
**Comfortable integrating AI with APIs, databases, Docker, web applications, and automation platforms.**

### Differentiator 6
**Strong persistence in debugging complex technical systems.**

---

# 33. Evidence-Based Skill Map

| Category | Skills / Technologies |
|---|---|
| Programming | Python, JavaScript, HTML, CSS, C |
| ML | Logistic Regression, Random Forest, XGBoost, Balanced Random Forest, Decision Trees, KNN, Perceptron |
| ML Evaluation | Precision, Recall, F1, Confusion Matrix, Threshold Optimization, Stratified Split |
| Imbalanced ML | SMOTE, Balanced Random Forest, Leakage Prevention |
| Data Science | pandas, NumPy, Matplotlib, Seaborn, Imputation, EDA |
| GenAI | LLMs, Prompting, Local LLMs, Gemini, Ollama, Hugging Face |
| RAG | Embeddings, Vector DB, Chroma, Document Ingestion, Retrieval |
| Agents | LangChain, LangGraph, Hermes, Tool Use, MCP Concepts |
| Automation | n8n, Browser Automation, Workflow Orchestration |
| OCR | Tesseract, PyMuPDF, pdfplumber, pdfminer, Pillow |
| Backend | Flask, Gunicorn, REST/API Integration |
| Frontend | HTML, CSS, JavaScript, React.js exposure |
| Databases | SQLite, MySQL, MariaDB |
| DevOps/Deployment | Docker, Render, Streamlit, Environment Configuration |
| Version Control | Git, GitHub |
| APIs | TwelveData, Upstox concepts, SAP OData, Government APIs |
| Visualization | Plotly, Matplotlib, Seaborn |
| Financial AI | Stock analytics, market data, trading-agent concepts |

---

# 34. Overall Skill Profile

## Core Identity

**Practical AI builder transitioning from a government-sector professional background into AI/ML engineering, with strongest interest in Agentic AI, Generative AI, automation, and applied machine learning.**

## Most Valuable Skill Combination

```text
Python
   +
Machine Learning
   +
LLMs
   +
RAG
   +
AI Agents
   +
Automation
   +
APIs
   +
Databases
   +
Docker / Deployment
```

## Engineering Character

**Problem-driven + hands-on + automation-oriented + persistent debugger + cross-stack learner.**

## Best Career Narrative

The strongest narrative is not:

> "I am learning AI."

It is:

> **"I build practical AI systems that combine machine learning, LLMs, agents, retrieval, APIs, databases, and automation to solve real-world problems."**

---

# 35. Embedding-Ready Summary

**Profile:** AI/ML-focused software engineer in transition from a government-sector professional background into Applied AI. Strongest interests are Agentic AI, Generative AI, AI automation, Machine Learning, and RAG. Experienced with Python, pandas, NumPy, Matplotlib, Seaborn, Logistic Regression, Random Forest, XGBoost, Balanced Random Forest, imbalanced classification, SMOTE, threshold optimization, precision/recall/F1, and data-leakage prevention. Built a vehicle insurance fraud detection model using BalancedRandomForestClassifier on a highly imbalanced dataset. Experienced with LLM experimentation using Ollama, Hugging Face, Gemini, Gemma, Qwen, DeepSeek and other local/cloud models. Strong interest and practical exposure in RAG, embeddings, vector databases, Chroma, document ingestion, AnythingLLM, local knowledge systems, agent memory, LangChain, LangGraph, Hermes, and MCP. Built/experimented with OCR and document-processing pipelines using n8n, Docker, Python, PyMuPDF, pdfplumber, pdfminer, Tesseract, pandas and openpyxl. Experienced with APIs, web scraping, government systems, financial APIs, TwelveData, stock-analysis applications, SQLite, MySQL, MariaDB, Flask, Gunicorn, Render, Streamlit, Git and GitHub. Strong problem-solving ability demonstrated through debugging Docker, YAML, OAuth, API, SSL/TLS, OCR, deployment, browser-automation and local-agent issues. Particularly interested in autonomous research agents, AI trading systems, intelligent document processing, large-scale government-process automation, and AI systems capable of retrieving information, reasoning, using tools and executing multi-step workflows. Best-fit career positioning: AI/ML Engineer, Applied AI Engineer, Generative AI Engineer, Agentic AI Engineer, LLM Engineer, AI Automation Engineer, or ML Engineer.

"""


def _spacer(h="1.25rem"):
    st.markdown(f'<div style="height:{h}"></div>', unsafe_allow_html=True)

def _run_indexing(bar, fn):
    """Run an indexing function with a live progress bar; honest error banner."""
    def _cb(n, total, sec):
        bar.progress(int(n * 100 / max(total, 1)),
                     text=f"Embedding chunk {n}/{total} · section: {sec}")
    try:
        meta = fn(_cb)
        bar.progress(100, text="✅ Indexing complete")
        st.session_state["clear_profile_box"] = True
        st.session_state["flash_msg"] = (f"✅ Indexed {meta['chunks']} chunks "
                                         f"({meta.get('new_embeds', 0)} new embeddings).")
        return meta
    except Exception as e:
        bar.empty()
        st.session_state["flash_msg"] = f"⚠️ Indexing failed: {type(e).__name__}: {str(e)[:180]}"
        return None


def _profile_uploader():
    with st.container(border=True):
        msg = st.session_state.pop("flash_msg", None)
        if msg:
            st.success(msg)

        st.markdown("**👤 My Profile** — powers Personalized mode & tailored resumes")
        prof = get_profile()
        if prof:
            st.caption(f"Profile loaded · {prof['chunks']} chunks · updated {prof['uploaded_at']}")
            c1, c2 = st.columns([6, 2], vertical_alignment="center")
            preview = prof["text"][:400] + ("…" if len(prof["text"]) > 400 else "")
            c1.markdown(f"<div class='td-summary'>{preview}</div>", unsafe_allow_html=True)
            if c2.button("🗑️ Remove profile", key="prof_del"):
                clear_profile()
                st.rerun()
        else:
            st.caption("No profile yet — paste your resume below, or load the demo profile with one click. "
                       "This unlocks Personalized mode on the Dashboard.")

        txt = st.text_area("Profile / resume text", height=180, key="profile_text")
        st.caption("💾 Save & Index = replace the WHOLE profile · "
                   "➕ Append = add this text to the existing profile · "
                   "📥 Demo = load & index the built-in sample resume.")

        b1, b2, b3 = st.columns(3)
        if b1.button("💾 Save & Index", width="stretch", key="prof_save"):
            if txt.strip():
                bar = st.progress(0, text="Chunking profile…")
                _run_indexing(bar, lambda cb: save_profile(txt, progress_cb=cb))
                st.rerun()
            else:
                st.warning("Paste your profile first.")

        if b2.button("➕ Append & Re-index", width="stretch", key="prof_append",
                     disabled=not bool(prof)):
            if txt.strip():
                bar = st.progress(0, text="Appending & re-indexing…")
                _run_indexing(bar, lambda cb: append_profile(txt, progress_cb=cb))
                st.rerun()
            else:
                st.warning("Paste the new data first.")

        if b3.button("📥 Load demo profile", width="stretch", key="prof_sample"):
            bar = st.progress(0, text="Loading & indexing demo profile…")
            meta = _run_indexing(bar, lambda cb: save_profile(SAMPLE_PROFILE,
                                                              source="demo",
                                                              progress_cb=cb))
            if meta:
                st.session_state["load_sample"] = True
            st.rerun()

def _resume_text(res):
    c = res.get("contact") or {}
    skills = res.get("skills") or []
    experience = res.get("experience") or []
    projects = res.get("projects") or []
    education = res.get("education") or []
    certs = res.get("certifications") or []
    langs = res.get("languages") or []
    gaps = res.get("gaps") or []

    lines = [
        c.get("name", ""),
        " | ".join(x for x in (c.get("location"), c.get("phone"), c.get("email")) if x),
        res.get("headline", ""),
        "",
        "PROFESSIONAL SUMMARY",
        res.get("summary", ""),
        "",
        "CORE COMPETENCIES & SKILLS",
        ", ".join(skills),
        "",
    ]
    if experience:
        lines.append("PROFESSIONAL EXPERIENCE")
        for exp in experience:
            lines.append(f"{exp.get('title', '')} | {exp.get('company', '')} | {exp.get('dates', '')}")
            for b in (exp.get("bullets") or []):
                lines.append(f"- {b}")
            lines.append("")
    if projects:
        lines.append("KEY PROJECTS")
        for proj in projects:
            lines.append(f"{proj.get('name', '')}")
            for b in (proj.get("bullets") or []):
                lines.append(f"- {b}")
            lines.append("")
    if education:
        lines.append("EDUCATION")
        for ed in education:
            sc = _fmt_score(ed.get("score"))
            lines.append(str(ed.get("degree") or "") +
                         ((" | " + str(ed.get("institution") or "")) if ed.get("institution") else ""))
            line2 = " | ".join(x for x in (sc, str(ed.get("year") or "")) if x)
            if line2:
                lines.append("    " + line2)
        lines.append("")
    if certs:
        lines.append("CERTIFICATIONS")
        for x in certs:
            lines.append(f"- {x}")
        lines.append("")
    if langs:
        lines.append("LANGUAGES")
        lines.append(", ".join(langs))
        lines.append("")
    if gaps:
        lines.append("AREAS FOR DEVELOPMENT (coaching only — exclude from submissions)")
        for g in gaps:
            lines.append(f"- {g}")
    return "\n".join(lines)


def _render_tailor(res):
    if res.get("error"):
        st.warning(res["error"])
        return
    fit = res.get("fit")
    fit_txt = f"{fit}% match" if fit is not None else "RAG active"

    st.markdown(
        f"<h3 style='margin:1.2rem 0 .6rem 0'>🎯 {res.get('company', '')} — {res.get('role', '')}"
        f"<span class='pill' style='background:#1B7F3B22;color:#1B7F3B'>{fit_txt}</span></h3>",
        unsafe_allow_html=True)

    with st.container(border=True):
        contact = res.get("contact") or {}
        st.markdown(f"<h4 style='margin:0; color:#16324F'>{contact.get('name', '')}</h4>",
                    unsafe_allow_html=True)
        cline = " | ".join(x for x in (contact.get("location"), contact.get("phone"),
                                       contact.get("email")) if x)
        if cline:
            st.caption(cline)
        st.markdown(f"<div style='font-weight:700;color:#44566C;margin:.3rem 0 .5rem 0'>{res.get('headline', '')}</div>",
                    unsafe_allow_html=True)
        st.write(res.get("summary", ""))

        skills = res.get("skills") or []
        if skills:
            st.markdown("<div class='th' style='margin-top:.8rem'>Core Competencies & Skills</div>",
                        unsafe_allow_html=True)
            pills = "".join(
                f"<span class='pill' style='background:#2563EB18;color:#2563EB;"
                f"margin:0 .5rem .4rem 0'>{k}</span>" for k in skills)
            st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)

        experience = res.get("experience") or []
        if experience:
            st.markdown("<div class='th' style='margin-top:1.2rem'>Professional Experience</div>",
                        unsafe_allow_html=True)
            for exp in experience:
                st.markdown(
                    f"<div style='font-weight:700;color:#16324F;margin-top:.6rem'>{exp.get('title', '')} "
                    f"<span style='font-weight:400;color:#68788C'>| {exp.get('company', '')} | {exp.get('dates', '')}</span></div>",
                    unsafe_allow_html=True)
                for b in (exp.get("bullets") or []):
                    st.markdown(f"<div class='td-summary' style='margin-bottom:.2rem'>• {b}</div>",
                                unsafe_allow_html=True)

        projects = res.get("projects") or []
        if projects:
            st.markdown("<div class='th' style='margin-top:1.2rem'>Key Projects</div>",
                        unsafe_allow_html=True)
            for proj in projects:
                st.markdown(f"<div style='font-weight:700;color:#16324F;margin-top:.6rem'>{proj.get('name', '')}</div>",
                            unsafe_allow_html=True)
                for b in (proj.get("bullets") or []):
                    st.markdown(f"<div class='td-summary' style='margin-bottom:.2rem'>• {b}</div>",
                                unsafe_allow_html=True)

        education = res.get("education") or []
        if education:
            st.markdown("<div class='th' style='margin-top:1.2rem'>Education</div>",
                        unsafe_allow_html=True)
            for ed in education:
                deg = str(ed.get("degree") or "")
                inst = str(ed.get("institution") or "")
                yr = str(ed.get("year") or "")
                sc = _fmt_score(ed.get("score"))
                line2 = "  |  ".join(x for x in (sc, yr) if x)
                st.markdown(
                    "<div class='td-summary' style='margin-bottom:.45rem'><b>" + deg + "</b>" +
                    ((" — " + inst) if inst else "") +
                    (("<br><span style='color:#68788C'>" + line2 + "</span>") if line2 else "") +
                    "</div>",
                    unsafe_allow_html=True)

        certs = res.get("certifications") or []
        if certs:
            st.markdown("<div class='th' style='margin-top:1.2rem'>Certifications</div>",
                        unsafe_allow_html=True)
            for x in certs:
                st.markdown(f"<div class='td-summary' style='margin-bottom:.2rem'>• {x}</div>",
                            unsafe_allow_html=True)

        langs = res.get("languages") or []
        if langs:
            st.markdown("<div class='th' style='margin-top:1.2rem'>Languages</div>",
                        unsafe_allow_html=True)
            st.markdown(f"<div class='td-summary'>{', '.join(langs)}</div>",
                        unsafe_allow_html=True)

        gaps = res.get("gaps") or []
        if gaps:
            st.markdown("<div class='th' style='margin-top:1.2rem'>Watch-outs (coaching only — not in exports)</div>",
                        unsafe_allow_html=True)
            for g in gaps:
                st.markdown(f"<div class='td-next' style='margin-bottom:.3rem'>➤ {g}</div>",
                            unsafe_allow_html=True)

        with st.expander("🔎 Retrieved profile evidence (RAG)"):
            for e in res.get("evidence", []):
                tag = "guaranteed" if e.get("score") == "core" else f"score {e.get('score', '')}"
                st.markdown(
                    f"<div class='td-summary' style='margin-bottom:.4rem'>"
                    f"<b>[{e.get('section', '')} · {tag}]</b> "
                    f"{e.get('text', '')}</div>",
                    unsafe_allow_html=True)

        with st.expander("📋 Plain-text resume (click to copy)", expanded=True):
            st.caption("Use the copy icon in the top-right corner of the box below, or highlight and copy manually.")
            st.code(_resume_text(res), language="text")

        d1, d2, d3 = st.columns(3)
        d1.download_button("⬇️ Download .docx",
                           data=build_docx(res),
                           file_name=f"resume_{res.get('jd_hash', 'jd')}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key="dl_docx")
        d2.download_button("⬇️ Download .pdf",
                           data=build_pdf(res),
                           file_name=f"resume_{res.get('jd_hash', 'jd')}.pdf",
                           mime="application/pdf",
                           key="dl_pdf")
        d3.download_button("⬇️ Download .txt",
                           data=_resume_text(res),
                           file_name=f"resume_{res.get('jd_hash', 'jd')}.txt",
                           mime="text/plain",
                           key="dl_txt")


def render():
    if st.session_state.pop("clear_profile_box", False):
        st.session_state["profile_text"] = ""
    if st.session_state.pop("load_sample", False):
        st.session_state["profile_text"] = SAMPLE_PROFILE

    st.markdown("""
    <style>
    .th{ color:#68788C; font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; font-weight:700; padding:.1rem 0 .45rem 0; }
    .td-summary{ font-size:.85rem; color:#44566C; line-height:1.5; }
    .td-next{ font-size:.85rem; font-weight:700; color:#EA580C; line-height:1.4; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='margin:.5rem 0 1rem 0'>📄 Resume Designer</h2>",
                unsafe_allow_html=True)

    _profile_uploader()
    _spacer()

    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False

    with st.container(border=True):
        st.markdown("**📋 Job Description** — paste the full JD you want to target")
        st.caption("The AI retrieves the most relevant parts of your profile "
                   "and writes a structured, ATS-friendly resume tailored to this exact job.")
        jd = st.text_area("Paste the job description here", height=220, key="jd_text")

        current_jd_hash = jd_hash(jd) if jd.strip() else None
        last_gen_hash = st.session_state.get("last_gen_hash")
        jd_unchanged = (current_jd_hash == last_gen_hash) and current_jd_hash is not None

        disable_gen = st.session_state.is_generating or not jd.strip() or jd_unchanged
        disable_force = st.session_state.is_generating or not jd.strip()

        c1, c2 = st.columns(2)
        gen_btn = c1.button("✨ Generate tailored resume", width="stretch",
                            key="gen_tailor", disabled=disable_gen)
        force_btn = c2.button("🔄 Force regenerate", width="stretch",
                              key="regen_tailor", disabled=disable_force)

        if jd_unchanged and not st.session_state.is_generating:
            st.caption("ℹ️ JD unchanged. Use 'Force regenerate' to trigger a fresh AI call.")

        if gen_btn:
            st.session_state.is_generating = True
            try:
                with st.spinner("Retrieving, drafting & polishing your resume..."):
                    st.session_state["tailor_res"] = tailor_for_jd(jd)
                    st.session_state["tailor_for"] = current_jd_hash
                    st.session_state["last_gen_hash"] = current_jd_hash
            finally:
                st.session_state.is_generating = False
                st.rerun()

        if force_btn:
            st.session_state.is_generating = True
            try:
                with st.spinner("Regenerating with fresh Gemini calls..."):
                    st.session_state["tailor_res"] = tailor_for_jd(jd, force=True)
                    st.session_state["tailor_for"] = current_jd_hash
                    st.session_state["last_gen_hash"] = current_jd_hash
            finally:
                st.session_state.is_generating = False
                st.rerun()

    res = st.session_state.get("tailor_res")
    if res and jd.strip() and res.get("jd_hash") == (current_jd_hash or ""):
        _render_tailor(res)