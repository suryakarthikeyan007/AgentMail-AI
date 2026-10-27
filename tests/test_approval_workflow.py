"""
Unit & Integration Tests for AgentMail AI Human Approval Workflow
Verifies:
- Approval dispatch & database state updates
- Duplicate send prevention (Issue #5)
- Rejection handling & audit trail
- Edit & re-verify pipeline
- State transition safety (preventing approval after rejection, preventing edit after dispatch)
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.db import (
    init_db,
    get_db_connection,
    add_to_approval_queue,
    save_processed_email,
    get_approval_queue,
    get_audit_logs
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


def create_mock_pending_email(message_id: str, sender: str = "recruiter@talent.io", subject: str = "Technical Interview"):
    """Helper to register a mock email in both processed_emails and approval_queue."""
    save_processed_email({
        "message_id": message_id,
        "thread_id": f"thread_{message_id}",
        "sender": sender,
        "subject": subject,
        "category": "Interview",
        "priority": "High",
        "planner_decision": "HUMAN_APPROVAL",
        "risk_level": "MEDIUM",
        "final_action": "HUMAN_APPROVAL",
        "response_body": "Tentative draft waiting approval",
        "approved": 0,
        "processing_time_ms": 950
    })

    add_to_approval_queue({
        "message_id": message_id,
        "thread_id": f"thread_{message_id}",
        "sender": sender,
        "subject": subject,
        "original_body": "Can you meet tomorrow at 3 PM?",
        "retrieved_context": "Calendar offline.",
        "draft_subject": f"Re: {subject}",
        "draft_body": "I have received your invitation and will verify my schedule.",
        "planner_decision": "HUMAN_APPROVAL",
        "risk_level": "MEDIUM",
        "reason": "Calendar availability is unverified."
    })


def test_approve_pending_email_success():
    msg_id = f"test_appr_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    res = client.post("/api/approval", json={
        "message_id": msg_id,
        "comment": "Supervisor verified and approved draft."
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["dispatch"]["sent"] is True

    # 1. Verify approval_queue status in DB
    items = get_approval_queue()
    matching = [i for i in items if i["message_id"] == msg_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "APPROVED"

    # 2. Verify processed_emails DB sync
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT approved, final_action FROM processed_emails WHERE message_id = ?", (msg_id,))
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row["approved"] == 1
    assert row["final_action"] == "APPROVED_AND_SENT"

    # 3. Verify audit log entry
    logs = get_audit_logs(limit=20)
    audit_entry = next((l for l in logs if l["message_id"] == msg_id), None)
    assert audit_entry is not None
    assert audit_entry["action"] == "APPROVED_AND_SENT"
    assert audit_entry["approval_status"] == "APPROVED"
    assert "SIMULATED" in audit_entry["send_status"] or audit_entry["send_status"] == "SENT"
    assert "provider_message_id" in data["dispatch"]


def test_duplicate_send_prevention():
    """ISSUE 5 FIX: Re-approving an already dispatched email MUST return 400."""
    msg_id = f"test_dupe_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    # First approval -> 200 OK
    res1 = client.post("/api/approval", json={"message_id": msg_id, "comment": "First Send"})
    assert res1.status_code == 200

    # Second approval attempt -> 400 Bad Request
    res2 = client.post("/api/approval", json={"message_id": msg_id, "comment": "Duplicate Send Attempt"})
    assert res2.status_code == 400
    assert "Duplicate transmission prevented" in res2.json()["detail"]


def test_reject_pending_email():
    msg_id = f"test_rej_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    res = client.post("/api/reject", json={
        "message_id": msg_id,
        "comment": "Supervisor rejected draft due to bad timing."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"

    # Verify DB status
    items = get_approval_queue()
    matching = [i for i in items if i["message_id"] == msg_id]
    assert matching[0]["status"] == "REJECTED"

    # Verify audit log
    logs = get_audit_logs(limit=20)
    audit_entry = next((l for l in logs if l["message_id"] == msg_id), None)
    assert audit_entry is not None
    assert audit_entry["action"] == "REJECTED_STOP"
    assert audit_entry["send_status"] == "NOT_SENT"


def test_cannot_approve_rejected_email():
    """Cannot approve an email that was already rejected."""
    msg_id = f"test_rejpending_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    client.post("/api/reject", json={"message_id": msg_id, "comment": "Rejecting"})
    res = client.post("/api/approval", json={"message_id": msg_id, "comment": "Trying to approve"})
    assert res.status_code == 400
    assert "Cannot approve a previously rejected" in res.json()["detail"]


def test_cannot_edit_rejected_email():
    """Item 4: Cannot edit an email draft that was already rejected."""
    msg_id = f"test_rejedit_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    client.post("/api/reject", json={"message_id": msg_id, "comment": "Rejecting"})
    res = client.post("/api/edit-response", json={
        "message_id": msg_id,
        "edited_body": "Attempted edit on rejected email",
        "comment": "Edit after rejection"
    })
    assert res.status_code == 400
    assert "Cannot edit or dispatch a previously rejected" in res.json()["detail"]


def test_cannot_re_reject_rejected_email():
    """Item 4: Repeated rejection clicks return 400 bad request."""
    msg_id = f"test_duprej_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    res1 = client.post("/api/reject", json={"message_id": msg_id, "comment": "Rejecting"})
    assert res1.status_code == 200

    res2 = client.post("/api/reject", json={"message_id": msg_id, "comment": "Rejecting again"})
    assert res2.status_code == 400
    assert "already been rejected" in res2.json()["detail"]


def test_cannot_reject_dispatched_email():
    """Cannot reject an email that was already sent."""
    msg_id = f"test_rejdispatched_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    client.post("/api/approval", json={"message_id": msg_id, "comment": "Approved"})
    res = client.post("/api/reject", json={"message_id": msg_id, "comment": "Trying to reject"})
    assert res.status_code == 400
    assert "Cannot reject an email draft that has already been dispatched" in res.json()["detail"]


def test_edit_response_workflow_and_duplicate_prevention():
    msg_id = f"test_edit_{uuid.uuid4().hex[:8]}"
    create_mock_pending_email(msg_id)

    safe_edited_body = (
        "Dear Recruiter,\n\n"
        "Thank you for the invitation. I have checked my availability and can confirm Wednesday at 4 PM.\n\n"
        "Best regards,\nPradeep Kumar A."
    )

    res = client.post("/api/edit-response", json={
        "message_id": msg_id,
        "edited_body": safe_edited_body,
        "comment": "Edited to specify confirmed Wednesday slot"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "edited_and_sent"
    assert "provider_message_id" in data["dispatch"]

    # Verify DB update
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT final_action, response_body, approved FROM processed_emails WHERE message_id = ?", (msg_id,))
    row = cursor.fetchone()
    conn.close()
    assert row["approved"] == 1
    assert row["final_action"] == "EDITED_AND_SENT"
    assert row["response_body"] == safe_edited_body

    # Duplicate edit prevention
    res2 = client.post("/api/edit-response", json={
        "message_id": msg_id,
        "edited_body": "Another edit attempt",
        "comment": "Duplicate edit"
    })
    assert res2.status_code == 400
    assert "already been dispatched. Further edits blocked." in res2.json()["detail"]


def test_health_check_endpoint():
    """ISSUE 6 TEST: Verifies that /api/health returns verified database and model service statuses."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "backend" in data
    assert data["backend"]["online"] is True
    assert "database" in data
    assert data["database"]["connected"] is True
    assert "ollama" in data
    assert "embedding" in data
    assert "test_mode" in data
