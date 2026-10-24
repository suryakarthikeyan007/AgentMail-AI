# AgentMail AI - Technical System Architecture Specification

## 1. Architectural Overview
AgentMail AI adopts a **Decoupled Multi-Agent Cognitive Architecture** optimized for local execution on Windows. The system separates classification, retrieval, memory recall, deliberative planning, draft generation, and safety verification into specialized, single-responsibility modules.

---

## 2. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Sender as External Sender (Gmail)
    participant GT as Gmail Trigger / Webhook
    participant EP as Email Preprocessor
    participant CA as Classifier Agent (Llama 3.1)
    participant RAG as RAG Retriever (nomic-embed-text)
    participant MEM as Conversation Memory (SQLite)
    participant PA as Planner Agent (Llama 3.1)
    participant SG as Safety Gate
    participant WA as Writer Agent (Llama 3.1)
    participant QC as Quality & Risk Critic
    actor Supervisor as Human Supervisor (Dashboard)
    participant GS as Gmail Dispatch (Safe Mode)

    Sender->>GT: Transmits Email
    GT->>EP: Ingests raw payload
    EP->>EP: Strips HTML, signatures, and quotes
    EP->>CA: Normalized Email Payload
    CA->>CA: Computes Category, Intent, Sensitivity (JSON)
    CA->>RAG: Queries relevant knowledge chunks
    RAG-->>PA: Top-k Grounding Passages
    CA->>MEM: Fetches thread history
    MEM-->>PA: Prior turns and entity context
    PA->>PA: Deliberates operational action
    
    alt Planner Decision: IGNORE
        PA->>SG: IGNORE
        SG->>MEM: Updates thread state
        SG-->>GT: Silent Halt
    else Planner Decision: AUTO_REPLY / CLARIFICATION / HUMAN_APPROVAL
        PA->>WA: Generates Draft Response
        WA-->>QC: Proposed Subject & Body
        QC->>QC: Evaluates Risk Level & Hallucinations
        QC-->>SG: Audit Report (Risk Level, Issues)
        
        alt Risk is HIGH or Decision is HUMAN_APPROVAL
            SG->>Supervisor: Places in Approval Queue
            Supervisor->>SG: Approve / Edit / Reject
            SG->>GS: Dispatches verified email
        else Risk is LOW and Decision is AUTO_REPLY
            SG->>GS: Autonomous Dispatch (Safe Mode)
        end
        
        GS->>MEM: Appends turn and response summary
        GS->>Sender: Dispatches Email
    end
```

---

## 3. Finite State Machine (FSM) Decision Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Ingestion
    Ingestion --> Preprocessed: HTML & Signature Stripping
    Preprocessed --> Classified: Llama 3.1 Classification
    Classified --> Contextualized: RAG Retrieval & Memory Recall
    Contextualized --> Planned: Deliberative Planner Agent
    
    state Planned {
        [*] --> EvaluatingRisk
        EvaluatingRisk --> IGNORE: Spam / Low-Value Pitch
        EvaluatingRisk --> TOOL_REQUIRED: External Service Needed
        EvaluatingRisk --> DRAFTING: Routine or Interactive Inquiry
    }
    
    DRAFTING --> QualityAudit: Draft Generated
    QualityAudit --> SafetyCheck: Risk Assessed (LOW/MED/HIGH)
    
    state SafetyCheck {
        [*] --> CheckGate
        CheckGate --> SafeAutoReply: Risk is LOW and Category Safe
        CheckGate --> EscalateHuman: Risk is HIGH or Sensitive (Salary/Dates)
    }
    
    EscalateHuman --> SupervisorReview: Added to Queue
    SupervisorReview --> Dispatched: Approved / Edited
    SupervisorReview --> Halted: Rejected by Supervisor
    
    SafeAutoReply --> Dispatched: TEST_MODE / Gmail API
    Dispatched --> UpdateMemory: State Persisted
    UpdateMemory --> [*]
    Halted --> [*]
    IGNORE --> [*]
```

---

## 4. RAG Pipeline Architecture

```text
┌──────────────────────────┐
│   knowledge_base/        │
│   ├── profile/           │
│   ├── resume/            │
│   ├── education/         │
│   ├── skills/            │
│   ├── projects/          │
│   ├── internships/       │
│   ├── professional/      │
│   └── response_rules/    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Semantic Chunking Engine │ (Max 150 words per cohesive block)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ nomic-embed-text (Ollama)│ (Generates 768-dim vector)
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ SQLite rag_chunks Table  │ (Stores chunk text + embedding JSON)
└────────────┬─────────────┘
             │ Cosine Similarity Search
             ▼
┌──────────────────────────┐
│ Top-2 Grounding Chunks   │ -> Injected into Planner, Writer & Critic Prompts
└──────────────────────────┘
```

---

## 5. Security & Boundary Isolation
1. **Untrusted Email Demarcation**: Email contents are framed inside isolated triple-quoted blocks with prompt-injection control filtering.
2. **Environment Variable Protection**: All credentials (`.env`) are kept out of frontend code.
3. **Safe Dispatch Switch**: `TEST_MODE=true` guarantees that during development, tests, and viva examinations, no emails can be dispatched to real third parties without explicit authorization.
