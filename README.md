# AgentMail AI: An Agentic AI-Based Intelligent Email Management System

[![Live Demo](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-brightgreen.svg?style=for-the-badge&logo=github)](https://suryakarthikeyan007.github.io/AgentMail-AI/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-0.32.8-black.svg)](https://ollama.com/)
[![Model: Llama 3.1](https://img.shields.io/badge/LLM-Llama_3.1_(8B)-green.svg)](https://ollama.com/library/llama3.1)
[![Embeddings: nomic-embed-text](https://img.shields.io/badge/Embeddings-nomic--embed--text-purple.svg)](https://ollama.com/library/nomic-embed-text)
[![n8n 2.8.4](https://img.shields.io/badge/n8n-2.8.4-red.svg)](https://n8n.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-teal.svg)](https://fastapi.tiangolo.com/)

> 🌐 **Live Interactive Web Demo**: **[https://suryakarthikeyan007.github.io/AgentMail-AI/](https://suryakarthikeyan007.github.io/AgentMail-AI/)**

A complete, production-grade final-year B.Tech Capstone Project in **Artificial Intelligence & Data Science**.

---

## 📌 Project Thesis & Novelty

> **"Our system does not simply generate an email reply. It decides what should happen next."**

Unlike naive chatbot wrappers that blindly draft replies to every incoming email, **AgentMail AI** executes an 8-stage agentic cognition lifecycle:

$$\text{CLASSIFY} \longrightarrow \text{RETRIEVE} \longrightarrow \text{REMEMBER} \longrightarrow \text{PLAN} \longrightarrow \text{DECIDE} \longrightarrow \text{ACT} \longrightarrow \text{VERIFY} \longrightarrow \text{REMEMBER}$$

The system operates across **5 deterministic decisions**:
1. `AUTO_REPLY`: Factual, safe, grounded responses.
2. `HUMAN_APPROVAL`: Sensitive, high-risk, or commitment-demanding emails (salary, meetings, legal).
3. `CLARIFICATION_REQUIRED`: Ambiguous requests lacking critical parameters.
4. `TOOL_REQUIRED`: Needs verified calendar, database, or workflow actions.
5. `IGNORE`: Unsolicited promotional spam and cold pitches.

---

## 🏗️ System Architecture

```text
GMAIL / WEBHOOK
      │
      ▼
Email Preprocessor (Strips HTML, signatures, and quotes)
      │
      ▼
Email Classifier Agent (Llama 3.1: Category, Intent, Priority, Sensitivity)
      │
      ├───────────────────────────────┬───────────────────────────────┐
      ▼                               ▼                               ▼
RAG Knowledge Retrieval     Conversation Memory             Tool Availability
 (nomic-embed-text)          (Gmail Thread ID)              (Calendar, DB)
      │                               │                               │
      └───────────────────────────────┼───────────────────────────────┘
                                      │
                                      ▼
                             Planner Agent (Llama 3.1)
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
        [IGNORE / TOOL]                              [AUTO / HUMAN / CLARIFY]
               │                                             │
               │                                             ▼
               │                                    Email Writer Agent
               │                                             │
               │                                             ▼
               │                                   Quality & Risk Critic
               │                                             │
               │                                             ▼
               │                                    Safety Gate & Override
               │                                             │
               │                                             ▼
               │                                   Human Review Queue (if HIGH risk)
               │                                             │
               ▼                                             ▼
          Silent Log                                Safe Dispatch Gate (TEST_MODE)
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      │
                                      ▼
                        Persistent Conversation Memory
                                      │
                                      ▼
                             SQLite Audit Logging
```

---

## 💻 System Prerequisites (Windows)

1. **Operating System**: Windows 10 or Windows 11 (64-bit).
2. **Python**: Python 3.10 to 3.12 ([Download Python](https://www.python.org/downloads/)). Check with:
   ```powershell
   python --version
   ```
3. **Ollama**: Local AI Runtime ([Download Ollama](https://ollama.com/download/windows)). Check with:
   ```powershell
   ollama --version
   ```
4. **n8n**: Node-based Workflow Engine ([Download Node.js](https://nodejs.org/)). Check with:
   ```powershell
   n8n --version
   ```

---

## ⚡ Quick Start: 3-Step Setup

### Step 1: Verify Ollama Models
Ensure both the LLM and Embedding models are present in Ollama:
```powershell
ollama list
```
You should see:
- `llama3.1:latest`
- `nomic-embed-text:latest`

If missing, pull them with:
```powershell
ollama pull llama3.1
ollama pull nomic-embed-text
```

### Step 2: Install Python Dependencies
Open PowerShell inside this directory (`c:\Users\Pradeepa\Downloads\Agentic AI email`) and run:
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Live Terminal Demo
Test the complete agentic pipeline with one command:
```powershell
python run_demo.py
```

---

## 🖥️ Launching the Web Dashboard

To launch the dark professional web dashboard:
```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
👉 **`http://localhost:8000`**

### Features of the Dashboard:
- **KPI Metrics Grid**: Live counters of Total Processed, Auto-Replies, Human Approvals, Ignored Spam, and Average Latency.
- **Agentic Track Visualizer**: Animated pipeline showing the active stage (1 to 8).
- **Interactive Demo Console**: Test arbitrary incoming emails or use one of the 5 quick-load presets:
  - 📅 **1. Interview Slot** $\rightarrow$ Tests Zero-Hallucination Gate (forces Human Approval).
  - 💰 **2. Salary Offer** $\rightarrow$ Tests Financial Protection (forces Human Approval).
  - 📄 **3. Send Resume** $\rightarrow$ Tests RAG Grounding (triggers Auto-Reply).
  - 🚫 **4. Promo Spam** $\rightarrow$ Tests Noise Filtering (triggers Ignore).
  - 🔄 **5. Thread Follow-up** $\rightarrow$ Tests Conversation Memory recall.
- **Human Review Queue**: Inspect flagged drafts, and click **Approve**, **Reject**, or **Edit & Re-Verify**!
- **Audit Table**: View every processed email with full risk ratings and timestamps.

---

## 🔄 n8n Workflow Integration

1. Start your local n8n instance in a separate PowerShell window:
   ```powershell
   n8n start
   ```
2. Open your browser at: **`http://localhost:5678`**.
3. In the top-right menu, select **Add Workflow > Import from File**.
4. Choose the file located at:
   ```text
   n8n/workflow/AgentMail_AI.json
   ```
5. To configure live Gmail triggers, follow our step-by-step guide in:
   ```text
   n8n/credentials-guide/GMAIL_OAUTH_SETUP.md
   ```

---

## 🧪 Running Automated Tests

### 1. Run Unit Tests (Preprocessor, Safety Gates, Quality Critic)
```powershell
pytest tests/test_preprocessor.py tests/test_safety_checker.py -v
```

### 2. Run the 10 Formal Academic Test Cases
```powershell
python tests/test_10_cases.py
```

### 3. Run the Empirical Benchmark Evaluation Suite
```powershell
python evaluate.py
```

---

## 📁 Project Directory Structure

```text
AgentMail-AI/
├── .env.example                 # Environment variables template
├── .env                         # Active local configuration
├── requirements.txt             # Python package dependencies
├── run_demo.py                  # Interactive terminal demonstration script
├── evaluate.py                  # Academic benchmark evaluation runner
├── README.md                    # This complete documentation guide
│
├── backend/
│   ├── config.py                # Single source of truth configuration
│   ├── main.py                  # FastAPI server and static dashboard mount
│   ├── pipeline.py              # Master 8-stage Agentic Pipeline Orchestrator
│   │
│   ├── agents/                  # Multi-Agent Subsystems
│   │   ├── base.py              # Ollama caller & JSON extractor
│   │   ├── preprocessor.py      # HTML, quote & signature cleaner
│   │   ├── classifier.py        # Llama 3.1 intent & category classifier
│   │   ├── planner.py           # Core executive decision agent
│   │   ├── writer.py            # Factual email response writer
│   │   └── quality_checker.py   # Adversarial critic & risk auditor
│   │
│   ├── rag/                     # Retrieval-Augmented Generation
│   │   ├── vector_store.py      # nomic-embed-text SQLite vector store
│   │   └── retriever.py         # Semantic similarity retriever
│   │
│   ├── memory/                  # Conversation Memory
│   │   └── conversation_memory.py # Thread-linked multi-turn SQLite memory
│   │
│   ├── safety/                  # Safety Architecture
│   │   └── safety_gate.py       # Zero-hallucination overrides & safe dispatch
│   │
│   ├── database/                # SQLite Storage
│   │   └── db.py                # Tables, queries, and audit logging
│   │
│   └── api/                     # REST Endpoints
│       ├── routes.py            # FastAPI route handlers
│       └── schemas.py           # Pydantic data models
│
├── knowledge_base/              # Grounding Knowledge Base
│   ├── profile/personal_profile.md
│   ├── resume/resume_summary.md
│   ├── education/academic_background.md
│   ├── skills/technical_skills.md
│   ├── projects/major_projects.md
│   ├── internships/internship_experience.md
│   ├── professional/certifications_and_achievements.md
│   └── response_guidelines/email_guidelines.md
│
├── dashboard/                   # Dark Professional AI Dashboard
│   ├── index.html               # Main dashboard HTML
│   ├── style.css                # Dark theme UI stylesheet
│   └── app.js                   # Reactive dashboard JavaScript
│
├── n8n/                         # n8n Automation Engine
│   ├── workflow/
│   │   └── AgentMail_AI.json    # Complete 16-node importable workflow
│   └── credentials-guide/
│       └── GMAIL_OAUTH_SETUP.md # Google Cloud OAuth setup guide
│
├── tests/                       # Test Suite
│   ├── test_calendar_verification.py # Grounding & calendar gate tests
│   ├── test_approval_workflow.py     # Approval queue, SHA-256 & health endpoint tests
│   ├── test_memory_and_rag_proof.py  # Thread memory continuity & RAG proof tests
│   ├── test_planner.py               # Deterministic planner gate unit tests
│   ├── test_preprocessor.py          # Preprocessor unit tests
│   ├── test_safety_checker.py        # Safety & quality critic unit tests
│   └── test_10_cases.py              # 10 formal academic test cases
│
└── docs/                        # Complete Final-Year Academic Deliverables
    ├── 01_PROJECT_REPORT.md     # 29-section complete capstone report
    ├── 02_SYSTEM_ARCHITECTURE.md# Technical architecture & sequence diagrams
    ├── 03_PPT_PRESENTATION_OUTLINE.md # 18-20 slides presentation outline
    ├── 04_VIVA_QUESTIONS_AND_ANSWERS.md # 45 comprehensive viva Q&A
    └── 05_EVALUATION_FRAMEWORK.md # Mathematical metrics & benchmarking
```

---

## 🛡️ Safety & Zero-Hallucination Guarantees (6 Core Safeguards)

AgentMail AI is engineered with deterministic safety gates:
1. **Calendar Verification Grounding**: When calendar tools are offline, the system strictly outputs `UNVERIFIED_CALENDAR_OFFLINE`. The Writer Agent is prohibited from claiming *"I have checked my schedule"*; it grounds replies with *"I will need to confirm my availability before committing to that time"* and requests 2-3 alternatives.
2. **Transparent Structured Traces**: Every pipeline step is structured into human-readable cards with an expandable `<details>` technical debug panel for examiners.
3. **Strict State & Timestamp Consistency**: Timestamps preserve complete formats (`8:15:38 PM`) with singular/plural-aware counters (`1 Record` vs `2 Records`).
4. **Explicit Multi-Dimensional Policy**: Separates `priority` (urgency), `risk_level` (severity), and `approval_required` (boolean enforced by backend rules).
5. **End-to-End Approval Verification**: Approval actions enforce duplicate-send protection, quality re-verification on edits, and draft SHA-256 fingerprint tracking (`delivery_status: "SIMULATED_SUCCESS"` / `"DELIVERED"`).
6. **Verified Service Health**: Real-time `/api/health` monitoring SQLite and Ollama, with clear client-side simulation labeling on static GitHub Pages hosting.

---

## 🎓 Final-Year Viva & Examination Guide

All documentation for your project presentation is available in `docs/`:
- **Complete Project Report**: [`docs/01_PROJECT_REPORT.md`](file:///c:/Users/Pradeepa/Downloads/Agentic%20AI%20email/docs/01_PROJECT_REPORT.md)
- **Architecture Diagrams**: [`docs/02_SYSTEM_ARCHITECTURE.md`](file:///c:/Users/Pradeepa/Downloads/Agentic%20AI%20email/docs/02_SYSTEM_ARCHITECTURE.md)
- **18-Slide PPT Presentation Outline**: [`docs/03_PPT_PRESENTATION_OUTLINE.md`](file:///c:/Users/Pradeepa/Downloads/Agentic%20AI%20email/docs/03_PPT_PRESENTATION_OUTLINE.md)
- **45 Viva Questions & Answers**: [`docs/04_VIVA_QUESTIONS_AND_ANSWERS.md`](file:///c:/Users/Pradeepa/Downloads/Agentic%20AI%20email/docs/04_VIVA_QUESTIONS_AND_ANSWERS.md)
- **Evaluation & Benchmarks**: [`docs/05_EVALUATION_FRAMEWORK.md`](file:///c:/Users/Pradeepa/Downloads/Agentic%20AI%20email/docs/05_EVALUATION_FRAMEWORK.md)

---

## 👥 Authors & Academic Credits
- **Project**: AgentMail AI (Final-Year Capstone Project)
- **Candidate**: Pradeep Kumar A.
- **Degree**: B.Tech Artificial Intelligence & Data Science
- **Department**: Department of Artificial Intelligence & Data Science
- **Academic Year**: 2025–2026
