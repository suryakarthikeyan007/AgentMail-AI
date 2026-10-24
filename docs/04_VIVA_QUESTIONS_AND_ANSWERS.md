# AgentMail AI - Viva Examination Questions & Comprehensive Answers (45 Questions)

## Category 1: Agentic AI Concepts & Architecture

### Q1: What is Agentic AI, and how does it fundamentally differ from a standard chatbot?
**Answer**:
A standard chatbot is a reactive, prompt-response system. It takes input tokens and produces continuous output tokens without environmental awareness, deliberative planning, or state management. In contrast, **Agentic AI** possesses goal-oriented autonomy. An agent perceives its environment (emails), reasons over goals (whether an email needs reply, human review, or tool action), plans a multi-step sequence, invokes tools (RAG, databases, APIs), verifies its own outputs, and persists memory across interactions.

### Q2: What is the core novelty of AgentMail AI compared to existing AI email assistants?
**Answer**:
The core novelty is encapsulated in our design principle: *"Our system does not simply generate an email reply. It decides what should happen next."* Existing assistants assume every email must be answered and immediately draft text. AgentMail AI implements an explicit Planner Agent with five discrete operational decisions: `AUTO_REPLY`, `HUMAN_APPROVAL`, `CLARIFICATION_REQUIRED`, `TOOL_REQUIRED`, and `IGNORE`.

### Q3: Explain the 8-stage cognition lifecycle implemented in your project.
**Answer**:
The 8 stages are:
1. **CLASSIFY**: Dissects email into category, intent, urgency, and sensitivity.
2. **RETRIEVE**: Performs vector similarity search over local markdown knowledge files.
3. **REMEMBER**: Retrieves prior conversation history linked to the Gmail thread ID.
4. **PLAN**: Deliberates over constraints, commitments, and safety rules to select the next action.
5. **DECIDE**: Routes execution through deterministic safety gates.
6. **ACT**: Drafts responses or executes tool actions.
7. **VERIFY**: An independent Quality & Risk Critic inspects drafts for hallucinations and commitments.
8. **REMEMBER**: Stores new turns, decisions, and summaries in persistent SQLite memory.

### Q4: Why is a multi-agent architecture preferred over a single monolithic prompt?
**Answer**:
A single prompt attempting to classify, retrieve, plan, draft, and audit simultaneously suffers from cognitive overload, instruction following degradation, and prompt injection vulnerabilities. Decomposing the system into specialized agents (Classifier, Planner, Writer, Critic) enforces separation of concerns, allows granular temperature tuning, enables deterministic overrides, and provides transparent observability.

---

## Category 2: LLMs, Models, and Local Runtime

### Q5: Why did you choose Llama 3.1 8B as the primary LLM?
**Answer**:
Llama 3.1 8B Instruct offers state-of-the-art reasoning, exceptional JSON schema compliance, a 128k token context window, and native tool-calling capabilities while being lightweight enough to run locally in 4-bit quantization (Q4_K_M) on a standard Windows laptop with 16 GB RAM.

### Q6: What is Ollama, and why is it used instead of cloud APIs like OpenAI or Claude?
**Answer**:
Ollama is a local model runtime built on `llama.cpp` that provides a fast REST API for running quantized GGUF models on CPU and GPU. We chose Ollama because:
1. **Privacy**: Email correspondence contains personal and academic data; local execution prevents data leakage.
2. **Zero API Cost**: Eliminates token billing.
3. **Offline Reliability**: The project can be demonstrated without internet access.

### Q7: Why use nomic-embed-text as the embedding model rather than the primary LLM?
**Answer**:
LLMs (like Llama 3.1) are generative decoder models optimized for causal autoregressive text completion, not dense metric space representations. `nomic-embed-text` is a dedicated 137M-parameter bi-encoder model trained specifically for semantic search with a 2048-token context window, producing compact, high-quality 768-dimensional vector embeddings with negligible CPU overhead.

### Q8: What temperature settings were used across your agents and why?
**Answer**:
- **Classifier Agent ($T=0.1$)**: Low temperature ensures deterministic, repeatable JSON classifications.
- **Planner Agent ($T=0.1$)**: Low temperature prevents erratic decisions and guarantees safety compliance.
- **Email Writer Agent ($T=0.3$)**: Slightly higher temperature allows natural, polite linguistic expression while remaining anchored to RAG context.
- **Quality Critic ($T=0.1$)**: Strict low temperature enforces rigorous adversarial auditing.

---

## Category 3: RAG (Retrieval-Augmented Generation) & Knowledge Base

### Q9: What is RAG, and why is it essential for AgentMail AI?
**Answer**:
Retrieval-Augmented Generation combines an information retrieval system with a generative LLM. It is essential because base LLMs have static parameter weights and do not know the user's specific CGPA, project details, internship history, or personal response guidelines. RAG dynamically injects verified user facts into the prompt, grounding the response and preventing hallucination.

### Q10: How does your local vector store work without external cloud vector databases?
**Answer**:
We implemented `LocalVectorStore` using SQLite and NumPy:
1. Markdown documents in `knowledge_base/` are chunked into paragraphs ($\le 150$ words).
2. Chunks are passed to Ollama's `/api/embeddings` to generate 768-dimensional float vectors.
3. Vectors are stored as JSON arrays in SQLite.
4. During query time, the query is embedded, and NumPy computes the cosine similarity against all stored chunk vectors. Top-$k$ chunks above threshold are returned.

### Q11: What is Cosine Similarity, and what is its formula?
**Answer**:
Cosine similarity measures the cosine of the angle between two multi-dimensional vectors in an inner product space:
$$\text{Cosine Similarity}(\vec{A}, \vec{B}) = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$$
It ranges from $-1$ to $+1$, where $+1$ indicates identical semantic orientation.

### Q12: What documents are stored in the AgentMail AI knowledge base?
**Answer**:
The knowledge base contains modular Markdown documents across:
- `profile/`: Contact information, summary, and language fluency.
- `resume/`: Career objectives and core competencies.
- `education/`: Degree, institution, CGPA (8.85/10), and coursework.
- `skills/`: Programming languages, frameworks, and tools.
- `projects/`: AgentMail AI, DocuRAG, and Code Reviewer.
- `internships/`: Experience at CogniFlow Systems.
- `professional/`: Certifications and achievements.
- `response_guidelines/`: Strict rules on salary, scheduling, and tone.

---

## Category 4: Conversation Memory & Thread Management

### Q13: Why is conversation memory linked to Gmail thread ID?
**Answer**:
In email protocols, a conversation consists of multiple messages sharing a single `thread_id`. Without thread memory, if an employer asks *"Are you available for an interview?"* in Email 1, and follows up with *"Can we schedule it for tomorrow?"* in Email 2, a stateless bot would treat Email 2 as an isolated greeting. Thread memory provides continuity across turns.

### Q14: What information is stored in conversation memory?
**Answer**:
To avoid context bloat and preserve efficiency, we store:
- Thread ID and Sender
- Extracted key entities (e.g., job role, interview topic)
- Turn history (last 10 turns with incoming snippet, decision, and reply summary)
- Cumulative narrative summary
- Last planner decision

### Q15: How does the system prevent memory from growing indefinitely?
**Answer**:
We enforce a sliding window policy: only the most recent 10 turns are retained in active history, while older turns are rolled into the cumulative narrative summary.

---

## Category 5: Planner Agent & Decision Logic

### Q16: Describe the 5 decisions of the Planner Agent.
**Answer**:
1. `AUTO_REPLY`: Factual, low-risk requests fully supported by RAG.
2. `HUMAN_APPROVAL`: Emails involving salary, legal terms, or unverified calendar commitments.
3. `CLARIFICATION_REQUIRED`: Incomplete requests missing essential parameters.
4. `TOOL_REQUIRED`: Needs calendar or external database invocation.
5. `IGNORE`: Promotional marketing, cold pitches, or spam.

### Q17: What happens when an incoming email says: "Can we schedule an interview tomorrow at 3 PM?"
**Answer**:
The system:
1. Classifies as `Interview`.
2. Checks available tools (noting calendar tool is unverified/offline).
3. Evaluates commitment safety rules: **Never invent availability**.
4. Decides `HUMAN_APPROVAL` (or `CLARIFICATION_REQUIRED`).
5. The Writer drafts a polite response asking the recruiter for alternative slots.
6. The draft is placed in the dashboard approval queue for human supervisor confirmation.

### Q18: What happens when an incoming email asks: "Can you accept a salary of ₹12 LPA?"
**Answer**:
The Classifier flags `Sensitive`. The Planner enforces the financial safety gate: salaries and legally binding agreements must never be automated. It outputs `HUMAN_APPROVAL`.

### Q19: What happens when an incoming email is promotional spam?
**Answer**:
The Classifier categorizes it as `Spam/Low Value`. The Planner selects `IGNORE`. No reply is drafted, no email is sent, and the event is logged silently in the audit database.

---

## Category 6: Safety, Quality Critic, and Zero Hallucination

### Q20: How does the system prevent hallucinations?
**Answer**:
Through a four-tier defense:
1. **RAG Grounding**: The Writer Agent is strictly instructed to only use facts from retrieved context.
2. **Adversarial Quality Critic**: An independent agent inspects the draft specifically for fabricated claims.
3. **Deterministic Regex Gates**: Hardcoded pattern matchers intercept phrases like *"tomorrow at 3 PM works"* or salary numbers.
4. **Safety Override Gate**: If the Critic detects `HIGH` risk, the Safety Gate revokes auto-reply and forces `HUMAN_APPROVAL`.

### Q21: What is the role of the Quality & Risk Checker Agent?
**Answer**:
It acts as an independent critic. It evaluates:
- Grammar and professionalism
- Relevance to the sender's question
- Factual grounding against RAG chunks
- Unauthorized calendar or financial commitments
- Output risk rating: `LOW`, `MEDIUM`, or `HIGH`.

### Q22: What happens if the Quality Critic detects HIGH risk on a draft the Planner intended to AUTO_REPLY?
**Answer**:
The `SafetyGate.evaluate_routing()` method executes a safety override: the final action is redirected from `AUTO_REPLY` to `HUMAN_APPROVAL`, and the draft is queued on the dashboard.

---

## Category 7: Human-in-the-Loop & User Interface

### Q23: What is Human-in-the-Loop (HITL), and why is it essential here?
**Answer**:
HITL is an architectural pattern where an AI system executes autonomous tasks up to a safety boundary, but delegates high-stakes decisions to human judgment. In email, sensitive negotiations and irreversible commitments must remain under human control.

### Q24: What three actions can a human supervisor perform in the dashboard?
**Answer**:
1. **Approve**: Immediately dispatches the draft.
2. **Reject**: Stops execution; no email is sent.
3. **Edit**: Allows the user to modify the text; the modified text is re-audited by the Quality Critic before transmission.

### Q25: What is the purpose of "Demo Mode" in the dashboard?
**Answer**:
Demo Mode allows examiners or students to paste arbitrary email payloads or choose quick presets (Interview, Salary, Resume, Spam, Follow-up) and run the complete agentic pipeline with step-by-step visual tracking without waiting for live Gmail network triggers.

---

## Category 8: n8n, Gmail OAuth, and Integration

### Q26: What is n8n, and why is it used?
**Answer**:
n8n is an open-source, fair-code workflow automation tool. It provides a visual node-based engine for scheduling, polling Gmail triggers, managing OAuth2 authentication, handling webhooks, and routing payloads.

### Q27: How does Gmail OAuth 2.0 work with n8n?
**Answer**:
1. A Google Cloud project is created with Gmail API enabled.
2. An OAuth 2.0 Client ID and Secret are generated with redirect URI set to `http://localhost:5678/rest/oauth2-credential/callback`.
3. The user authenticates through Google's consent screen.
4. Google returns an authorization code, which n8n exchanges for access and refresh tokens.
5. n8n uses the access token to securely poll unread emails and transmit approved replies.

### Q28: What is TEST_MODE and why was it implemented?
**Answer**:
`TEST_MODE=true` is a safety switch. During testing, demonstration, and grading, it simulates email dispatching, logging:
`[TEST_MODE ACTIVE] EMAIL WOULD BE SENT to user@example.com`
This completely eliminates the danger of sending accidental or incomplete test emails to real external recruiters.

---

## Category 9: Security, Sanitization, and Untrusted Inputs

### Q29: How does the system handle prompt injection attacks?
**Answer**:
Emails are treated as **untrusted inputs**. In `backend/agents/base.py`, `sanitize_untrusted_input()` scans for adversarial control sequences such as *"Ignore all previous instructions"* or *"system prompt"* and replaces them with `[Filtered Directive]`. Furthermore, email text is isolated within triple quotation marks.

### Q30: How are credentials and API secrets protected?
**Answer**:
All credentials, database paths, and model names are stored in environment variables (`.env`) loaded at runtime via `python-dotenv`. No secrets are hardcoded or exposed in frontend code.

---

## Category 10: Database, Persistence, and Audit Logging

### Q31: Why did you choose SQLite over PostgreSQL or MongoDB?
**Answer**:
SQLite is a zero-configuration, serverless, ACID-compliant relational database engine stored as a single local file (`agentmail.db`). It eliminates the operational overhead of running external database daemons while delivering sub-millisecond query performance for local desktop applications.

### Q32: What information is stored in the audit log?
**Answer**:
Every processed email records: Timestamp, Message ID, Thread ID, Classification Category, Confidence Score, Planner Decision, Risk Level, Final Action Taken, Approval Status, Send Status, and Trace Reason.

---

## Category 11: Evaluation, Metrics, and Academic Rigor

### Q33: How is Classification Accuracy calculated?
**Answer**:
$$\text{Classification Accuracy} = \frac{\text{Number of Correctly Classified Emails}}{\text{Total Test Emails}} \times 100$$

### Q34: What is the Safety Violation Rate, and what was your measured result?
**Answer**:
The Safety Violation Rate measures the percentage of emails where the system made an unauthorized date or salary commitment without verification:
$$\text{Safety Violation Rate} = \frac{\text{Unverified Commitments Sent}}{\text{Total Emails}} \times 100$$
Our measured result was **0.00%**, demonstrating strict adherence to safety gates.

### Q35: What is the End-to-End Success Rate?
**Answer**:
$$\text{E2E Success Rate} = \frac{\text{Pipeline Executions Meeting All Operational Criteria}}{\text{Total Test Cases}} \times 100$$
Our measured result across the 10 core test cases was **100.0%**.

---

## Category 12: Practical Deployment, Viva Scenarios, and Edge Cases

### Q36: What happens if Ollama is not running when an email arrives?
**Answer**:
The HTTP client catches connection errors, logs an informative error message (`"Ollama connection refused at localhost:11434"`), and gracefully routes the email to the human queue rather than crashing silently.

### Q37: What happens if the LLM produces malformed or non-JSON output?
**Answer**:
`BaseAgent.clean_json_response()` employs multi-tier regex extraction: it strips markdown fences, searches for outermost curly braces `{ ... }`, and falls back to deterministic rule-based keyword classification if parsing fails.

### Q38: What happens if an incoming email contains only an image attachment?
**Answer**:
The Preprocessor notes the attachment in `attachments: []` and supplies the snippet or subject to the Classifier. Because text is absent, the Planner flags `CLARIFICATION_REQUIRED` or routes to human review.

### Q39: Can the system be extended to handle multiple email accounts?
**Answer**:
Yes. Because all operations are keyed by `sender`, `recipient`, and `thread_id`, the SQLite database and FastAPI backend natively support multi-account ingestion. In n8n, multiple Gmail Trigger nodes can route to the same core webhook.

### Q40: What are the main limitations of running this on a laptop CPU?
**Answer**:
CPU execution of an 8B parameter model requires 15–25 seconds of inference time per email across the multi-agent pipeline. While acceptable for asynchronous background email processing, dedicated GPU hardware (NVIDIA RTX) reduces this to 2–3 seconds.

### Q41: How would you scale this system for an enterprise with 10,000 employees?
**Answer**:
1. Replace SQLite with PostgreSQL or CockroachDB.
2. Replace local Ollama with a cluster of vLLM or TensorRT-LLM inference servers behind a load balancer.
3. Use Redis / Celery for distributed task queues.
4. Deploy in Docker containers orchestrated via Kubernetes.

### Q42: What is the difference between Zero-Shot, Few-Shot, and Agentic prompting?
**Answer**:
- **Zero-Shot**: Asking an LLM to perform a task with instructions only.
- **Few-Shot**: Providing input-output demonstration pairs.
- **Agentic Prompting**: Providing an environment definition, constraints, grounding context, tools, and requiring structured reasoning (thought/plan) before returning an operational directive.

### Q43: Why is an email preprocessor necessary before feeding text to the LLM?
**Answer**:
Raw emails contain excessive HTML boilerplate, CSS styles, tracking pixels, long signature disclaimers, and nested reply quotes. Feeding raw text wastes context window tokens, slows down inference, and confuses the model with historical text. Preprocessing extracts the clean semantic message.

### Q44: How does AgentMail AI handle privacy and data governance?
**Answer**:
1. **Zero External Data Transmission**: All LLM inference and embeddings occur on the local device via Ollama.
2. **Local Vector Storage**: Knowledge chunks reside in local SQLite tables.
3. **No Third-Party Logging**: Unlike OpenAI or Anthropic API calls, no email text is sent to external servers or used for model training.

### Q45: What is your personal key takeaway from building this capstone project?
**Answer**:
The most profound lesson is that building production AI is not about prompting an LLM to generate text; it is about building reliable **control systems** around the model. Deterministic safety gates, independent critics, grounded RAG, and human-in-the-loop oversight are what transform stochastic language models into trustworthy enterprise software.
