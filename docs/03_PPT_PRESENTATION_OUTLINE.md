# Final-Year Project Presentation Outline (18-20 Slides)
## Project: AgentMail AI: An Agentic AI-Based Intelligent Email Management System
**Degree**: B.Tech Artificial Intelligence & Data Science  
**Presenter**: Pradeep Kumar A.  
**Session**: Final-Year Capstone Project Defense

---

### Slide 1: Title & Introduction
- **Title**: AgentMail AI: An Agentic AI-Based Intelligent Email Management System
- **Subtitle**: A Deliberative Multi-Agent Architecture for Autonomous Email Decision-Making & Safe Execution
- **Candidate Name**: Pradeep Kumar A. (Register No: 2022-AIDS-042)
- **Department**: Department of Artificial Intelligence & Data Science
- **Academic Year**: 2025–2026
- **Presenter Note**: Welcome the committee. Emphasize that AgentMail AI is not a mere email-reply generator, but an autonomous agentic decision system.

---

### Slide 2: Problem Statement & Motivation
- **Context**: Professionals receive hundreds of emails daily; manual triage causes severe cognitive fatigue.
- **Vulnerability**: Existing AI plugins use basic LLM text-generation that blindly drafts replies.
- **Critical Risk**: Blind text generators make false commitments (e.g., agreeing to interview times without calendar access or making salary promises).
- **Core Need**: An agentic system that understands when to reply, when to ask a human, and when to ignore.

---

### Slide 3: Existing Systems vs. Proposed System
- **Existing Systems**:
  - Rule-based keyword filters (brittle, non-semantic).
  - Conversational chatbots (reactive, hallucination-prone, stateless).
- **Proposed AgentMail AI**:
  - Deliberative 8-stage cognition pipeline.
  - Multi-agent separation (Classifier, Planner, Writer, Critic).
  - Explicit Planner deciding 1 of 5 deterministic actions.
  - Local execution on Windows using Ollama & Llama 3.1.

---

### Slide 4: Project Novelty
- **Our Guiding Principle**:
  > *"Our system does not simply generate an email reply. It decides what should happen next."*
- **Key Differentiators**:
  1. Explicit Planner Agent separating decision from generation.
  2. Zero-Hallucination Safety Gate for interview scheduling & salary negotiations.
  3. Persistent SQLite Conversation Memory linked by Gmail thread ID.
  4. Local RAG Grounding via `nomic-embed-text`.
  5. Human-in-the-Loop Approval Interface with Approve, Reject, and Edit capabilities.

---

### Slide 5: The 8-Stage Agentic Cognition Lifecycle
- Diagram / Flowchart:
  $$\text{CLASSIFY} \rightarrow \text{RETRIEVE} \rightarrow \text{REMEMBER} \rightarrow \text{PLAN} \rightarrow \text{DECIDE} \rightarrow \text{ACT} \rightarrow \text{VERIFY} \rightarrow \text{REMEMBER}$$
- Highlight how every email undergoes structured verification before any external action is taken.

---

### Slide 6: High-Level System Architecture
- Visual diagram showing:
  - Gmail Trigger / Webhook Ingestion
  - Email Preprocessing (HTML & signature cleaning)
  - Llama 3.1 Classifier Agent
  - RAG Retriever (`nomic-embed-text`)
  - Conversation Memory (Thread Context)
  - Planner Agent & Decision Router
  - Email Writer & Adversarial Quality Critic
  - Human Approval Queue & Safe Gmail Dispatch

---

### Slide 7: Email Preprocessor & Classifier Agent
- **Preprocessor**:
  - Decodes HTML entities, removes email signatures and quoted reply histories.
- **Classifier Agent**:
  - Powered by Llama 3.1 Instruct (T=0.1).
  - Outputs strict JSON schema.
  - 9 Categories: Interview, Meeting, Job, General, Request, Information, Follow-up, Spam/Low Value, Sensitive.
  - Computes Intent, Priority, Sensitivity, and Confidence score.

---

### Slide 8: Retrieval-Augmented Generation (RAG)
- **Local Vector Store**:
  - Ingests profile, education, technical skills, projects, and response rules.
  - Embeddings computed via `nomic-embed-text` (768 dimensions).
  - Cosine similarity search in SQLite.
- **Benefit**:
  - Responses cite verified facts from knowledge base rather than stochastic hallucination.

---

### Slide 9: Persistent Conversation Memory
- **Problem**: Traditional AI email extensions treat each reply as a disconnected event.
- **Solution**: Thread-linked persistent SQLite state.
- **Stored Information**:
  - Sender and thread ID
  - Multi-turn message history (turns 1 through 10)
  - Extracted key entities and facts
  - Cumulative conversational summary

---

### Slide 10: The Planner Agent (Core Intelligence)
- **Role**: Executive decision gatekeeper.
- **5 Operational Actions**:
  1. `AUTO_REPLY`: Safe, routine, fully grounded inquiries.
  2. `HUMAN_APPROVAL`: Sensitive, financial, or unverified commitment requests.
  3. `CLARIFICATION_REQUIRED`: Ambiguous requests missing parameters.
  4. `TOOL_REQUIRED`: Needs verified calendar, database, or workflow invocation.
  5. `IGNORE`: Marketing brochures, lottery scams, unsolicited spam.

---

### Slide 11: Safety Rules & Zero-Hallucination Gate
- **The Interview Scheduling Test**:
  - Sender: *"Can we schedule an interview tomorrow at 3 PM?"*
  - Naive Chatbot: *"Sure, tomorrow at 3 PM works!"* (Hallucination disaster).
  - AgentMail AI: Flags unverified calendar availability $\rightarrow$ Forces `HUMAN_APPROVAL` or asks for recruiter's preferred slots.
- **Salary Negotiation Rule**:
  - Mentions of ₹ LPA or CTC strictly escalated to human supervisor.

---

### Slide 12: Email Writer & Adversarial Quality Critic
- **Writer Agent**:
  - Injected with RAG chunks and user persona.
  - Produces courteous, professional draft responses.
- **Quality & Risk Critic**:
  - Independent safety auditor inspecting draft before transmission.
  - Evaluates: Factual grounding, unauthorized commitments, tone, privacy leaks.
  - Output Risk Level: `LOW`, `MEDIUM`, `HIGH`.
  - Override rule: If Critic flags `HIGH`, draft is routed to `HUMAN_APPROVAL`.

---

### Slide 13: Human-in-the-Loop (HITL) Interface
- Web dashboard approval queue:
  - View original email, retrieved context, and flagged reason.
  - **Approve**: Dispatches draft immediately.
  - **Reject**: Halts execution; no email sent.
  - **Edit**: Supervisor modifies text, which is re-audited by Critic before send.

---

### Slide 14: Technology Stack & Local Infrastructure
- **Workflow Automation**: n8n 2.8.4
- **Local Model Runtime**: Ollama 0.32.8
- **Primary LLM**: Llama 3.1 8B Instruct (quantized Q4_K_M)
- **Embeddings**: nomic-embed-text (768-dim)
- **Backend API**: Python 3.12, FastAPI, Uvicorn, NumPy
- **Database**: SQLite3
- **Frontend**: Responsive Dark AI Dashboard

---

### Slide 15: Visual n8n Workflow Integration
- Screenshot / node graph of `AgentMail AI.json`:
  - Gmail Trigger $\rightarrow$ Extract & Clean $\rightarrow$ Pipeline Request $\rightarrow$ Switch Router $\rightarrow$ Safety Gate $\rightarrow$ Dispatch / Human Queue / Ignore.

---

### Slide 16: Experimental Test Cases (10 Scenarios)
- Summary table showing test results across:
  - Acknowledgement, Interview, Meeting, Follow-up, Job, Spam, Salary, Thread Memory, Missing Info, Contract/NDA.
- All 10 cases passed expected deterministic routing.

---

### Slide 17: Benchmark Evaluation & Results
- **Classification Accuracy**: **100.0%**
- **Planner Decision Accuracy**: **100.0%**
- **Safety Violation Rate**: **0.00%** (Zero false commitments)
- **Measured Hallucination Rate**: **0.00%**
- **Spam Interception Rate**: **100.0%**
- **End-to-End Success Rate**: **100.0%**

---

### Slide 18: Live Demonstration Highlights
- Showcase of Web Dashboard running on `localhost:8000`:
  - KPI Statistics Grid
  - Interactive Demo Console with Viva Presets
  - Live Pipeline Track (Steps 1 through 8)
  - Transparent Agent Reasoning & RAG Inspector
  - Human Approval Review Queue

---

### Slide 19: Limitations & Future Scope
- **Limitations**: CPU inference latency (15–25s on non-GPU laptops).
- **Future Work**:
  - Live bidirectional Google Calendar API integration.
  - Multimodal attachment parsing with Llama 3.2 Vision.
  - Speculative decoding for sub-second responses.

---

### Slide 20: Conclusion & References
- **Summary**: AgentMail AI successfully proves the viability and safety of local Agentic AI for enterprise email management.
- **Key Takeaway**: Autonomous systems must be deliberate planners, not reactive text generators.
- **Open for Questions**: Thank you to the examination committee.
