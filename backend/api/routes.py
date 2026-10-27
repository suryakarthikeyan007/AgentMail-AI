"""
AgentMail AI - FastAPI Route Handlers
Implements all required REST endpoints for email processing, dashboard metrics,
conversation memory retrieval, audit logs, and human-in-the-loop approvals.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import EmailInputSchema, ApprovalActionSchema, EditResponseSchema
from backend.pipeline import EmailAgentPipeline
from backend.rag.vector_store import LocalVectorStore
from backend.memory.conversation_memory import ConversationMemoryManager
from backend.safety.safety_gate import SafetyGate
from backend.agents.quality_checker import QualityRiskCheckerAgent
from backend.database.db import (
    get_processed_emails,
    get_system_stats,
    get_audit_logs,
    get_approval_queue,
    update_approval_status,
    insert_audit_log,
    get_db_connection
)

router = APIRouter()
pipeline = EmailAgentPipeline()
vector_store = LocalVectorStore()
memory_manager = ConversationMemoryManager()
safety_gate = SafetyGate()
quality_checker = QualityRiskCheckerAgent()


@router.post("/process-email", summary="Process incoming email through the full agentic pipeline")
def process_email_endpoint(payload: EmailInputSchema):
    try:
        raw_dict = payload.model_dump()
        result = pipeline.process_email(raw_dict)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")


@router.get("/emails", summary="Retrieve recent processed emails")
def get_emails_endpoint(limit: int = Query(50, ge=1, le=200)):
    try:
        emails = get_processed_emails(limit=limit)
        return {"count": len(emails), "emails": emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get system-wide summary metrics for dashboard")
def get_stats_endpoint():
    try:
        stats = get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/{thread_id}", summary="Fetch persistent conversation memory for a thread")
def get_thread_memory_endpoint(thread_id: str):
    memory = memory_manager.get_thread_memory(thread_id)
    if not memory:
        return {"thread_id": thread_id, "exists": False, "message": "No memory recorded for this thread."}
    return {"thread_id": thread_id, "exists": True, "data": memory}


@router.get("/audit", summary="Get audit logs")
def get_audit_endpoint(limit: int = Query(50, ge=1, le=200)):
    try:
        logs = get_audit_logs(limit=limit)
        return {"count": len(logs), "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals", summary="Get pending human approval items")
def get_approvals_endpoint(status: Optional[str] = None):
    try:
        items = get_approval_queue(status=status)
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approval", summary="Approve a pending human review draft and send")
def approve_draft_endpoint(payload: ApprovalActionSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approval_queue WHERE message_id = ?", (payload.message_id,))
    item = cursor.fetchone()

    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Approval item not found")

    item_dict = dict(item)

    # DUPLICATE SEND PREVENTION GATE
    if item_dict.get("status") in ["APPROVED", "EDITED_AND_APPROVED"]:
        conn.close()
        raise HTTPException(status_code=400, detail="This email draft has already been approved and sent. Duplicate transmission prevented.")

    if item_dict.get("status") == "REJECTED":
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot approve a previously rejected email draft.")

    # Dispatch email
    dispatch = safety_gate.dispatch_email(
        recipient=item_dict["sender"],
        subject=item_dict["draft_subject"],
        body=item_dict["edited_body"] or item_dict["draft_body"],
        thread_id=item_dict["thread_id"]
    )

    update_approval_status(payload.message_id, "APPROVED")

    # Update processed_emails state with delivery status
    cursor.execute("""
        UPDATE processed_emails
        SET approved = 1, final_action = 'APPROVED_AND_SENT', delivery_status = ?
        WHERE message_id = ?
    """, (dispatch.get("delivery_status", "SENT"), payload.message_id))
    conn.commit()
    conn.close()

    insert_audit_log(
        message_id=payload.message_id,
        thread_id=item_dict["thread_id"],
        classification="HumanApproved",
        confidence=1.0,
        planner_decision=item_dict["planner_decision"],
        risk_level=item_dict["risk_level"],
        action="APPROVED_AND_SENT",
        approval_status="APPROVED",
        send_status=dispatch.get("delivery_status", "SENT"),
        reason=f"Approved by supervisor. Delivery: {dispatch.get('delivery_status')}. Exact draft SHA: {dispatch.get('body_sha256')}. {payload.comment}".strip()
    )

    return {"status": "approved", "delivery_status": dispatch.get("delivery_status"), "dispatch": dispatch}


@router.post("/reject", summary="Reject a pending draft and stop execution")
def reject_draft_endpoint(payload: ApprovalActionSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approval_queue WHERE message_id = ?", (payload.message_id,))
    item = cursor.fetchone()

    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Approval item not found")

    item_dict = dict(item)
    if item_dict.get("status") in ["APPROVED", "EDITED_AND_APPROVED"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot reject an email draft that has already been dispatched.")

    update_approval_status(payload.message_id, "REJECTED")

    # Update processed_emails state
    cursor.execute("""
        UPDATE processed_emails
        SET final_action = 'REJECTED_STOP'
        WHERE message_id = ?
    """, (payload.message_id,))
    conn.commit()
    conn.close()

    insert_audit_log(
        message_id=payload.message_id,
        thread_id=item_dict["thread_id"],
        classification="HumanRejected",
        confidence=1.0,
        planner_decision=item_dict["planner_decision"],
        risk_level=item_dict["risk_level"],
        action="REJECTED_STOP",
        approval_status="REJECTED",
        send_status="NOT_SENT",
        reason=f"Rejected by supervisor. {payload.comment}".strip()
    )

    return {"status": "rejected", "message": "Email draft rejected. No message was dispatched."}


@router.post("/edit-response", summary="Submit modified email draft, re-verify via quality checker, and send")
def edit_response_endpoint(payload: EditResponseSchema):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM approval_queue WHERE message_id = ?", (payload.message_id,))
    item = cursor.fetchone()

    if not item:
        conn.close()
        raise HTTPException(status_code=404, detail="Approval item not found")

    item_dict = dict(item)

    if item_dict.get("status") in ["APPROVED", "EDITED_AND_APPROVED"]:
        conn.close()
        raise HTTPException(status_code=400, detail="This draft has already been dispatched. Further edits blocked.")

    # Re-audit edited body via Quality Risk Checker
    edited_draft = {
        "subject": item_dict["draft_subject"],
        "body": payload.edited_body
    }
    re_audit = quality_checker.audit(
        draft_response=edited_draft,
        original_email={"body": item_dict["original_body"]},
        rag_context=item_dict.get("retrieved_context", ""),
        memory_context="",
        planner_decision=item_dict["planner_decision"]
    )

    if re_audit.get("risk_level") == "HIGH":
        conn.close()
        return {
            "status": "warning",
            "message": "Edited body contains HIGH risk factors. Dispatch blocked.",
            "audit": re_audit
        }

    # Dispatch verified edited draft
    dispatch = safety_gate.dispatch_email(
        recipient=item_dict["sender"],
        subject=item_dict["draft_subject"],
        body=payload.edited_body,
        thread_id=item_dict["thread_id"]
    )

    update_approval_status(payload.message_id, "EDITED_AND_APPROVED", edited_body=payload.edited_body)

    # Update processed_emails record
    cursor.execute("""
        UPDATE processed_emails
        SET approved = 1, final_action = 'EDITED_AND_SENT', response_body = ?, delivery_status = ?
        WHERE message_id = ?
    """, (payload.edited_body, dispatch.get("delivery_status", "SENT"), payload.message_id))
    conn.commit()
    conn.close()

    insert_audit_log(
        message_id=payload.message_id,
        thread_id=item_dict["thread_id"],
        classification="HumanEdited",
        confidence=1.0,
        planner_decision=item_dict["planner_decision"],
        risk_level=re_audit.get("risk_level", "LOW"),
        action="EDITED_AND_SENT",
        approval_status="APPROVED",
        send_status=dispatch.get("delivery_status", "SENT"),
        reason=f"Edited by supervisor and re-verified. Delivery: {dispatch.get('delivery_status')}. Hash: {dispatch.get('body_sha256')}. {payload.comment}".strip()
    )

    return {"status": "edited_and_sent", "delivery_status": dispatch.get("delivery_status"), "dispatch": dispatch, "re_audit": re_audit}


@router.post("/rag/reindex", summary="Re-index local knowledge base markdown documents")
def reindex_rag_endpoint():
    try:
        count = vector_store.index_knowledge_base(force_reindex=True)
        return {"status": "success", "indexed_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Check verified real-time backend health, Ollama status, and database connectivity")
def get_health_endpoint():
    """Returns live verified health status of backend, database, and local Ollama model services."""
    # 1. Database check
    db_healthy = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_healthy = True
        conn.close()
    except Exception:
        db_healthy = False

    # 2. Ollama connection check
    ollama_healthy = False
    models_available = []
    try:
        import httpx
        with httpx.Client(timeout=3.0) as client:
            res = client.get("http://localhost:11434/api/tags")
            if res.status_code == 200:
                ollama_healthy = True
                models_available = [m.get("name") for m in res.json().get("models", [])]
    except Exception:
        ollama_healthy = False

    from backend.config import TEST_MODE, LLM_MODEL, EMBEDDING_MODEL
    return {
        "status": "healthy" if db_healthy else "degraded",
        "backend": {
            "online": True,
            "version": "2.0.0",
            "environment": "local"
        },
        "database": {
            "connected": db_healthy,
            "type": "SQLite (agentmail.db)"
        },
        "ollama": {
            "connected": ollama_healthy,
            "active_model": LLM_MODEL,
            "installed_models": models_available
        },
        "embedding": {
            "status": "active" if ollama_healthy and any("embed" in m for m in models_available) else ("offline" if not ollama_healthy else "ready"),
            "model": EMBEDDING_MODEL
        },
        "execution_mode": "TEST_MODE_SIMULATION" if TEST_MODE else "LIVE_GMAIL_API",
        "test_mode": TEST_MODE
    }
