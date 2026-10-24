"""
AgentMail AI - SQLite Database Layer
Handles persistent audit logging, processed emails, conversation memory, and human approval queue.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.config import DATABASE_PATH


def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with dict-like row access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the SQLite schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for full processed emails
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            thread_id TEXT,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            body_clean TEXT,
            category TEXT,
            intent TEXT,
            priority TEXT,
            confidence REAL,
            planner_decision TEXT,
            risk_level TEXT,
            final_action TEXT,
            approved INTEGER DEFAULT 0,
            response_subject TEXT,
            response_body TEXT,
            reasoning_summary TEXT,
            processing_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for thread-linked conversation memory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT UNIQUE,
            sender TEXT,
            subject TEXT,
            summary TEXT,
            key_facts TEXT,
            last_classification TEXT,
            last_decision TEXT,
            message_history TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for structured audit logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_id TEXT,
            thread_id TEXT,
            classification TEXT,
            confidence REAL,
            planner_decision TEXT,
            risk_level TEXT,
            action TEXT,
            approval_status TEXT,
            send_status TEXT,
            reason TEXT
        )
    """)

    # Table for human approval queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approval_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            thread_id TEXT,
            sender TEXT,
            subject TEXT,
            original_body TEXT,
            retrieved_context TEXT,
            draft_subject TEXT,
            draft_body TEXT,
            planner_decision TEXT,
            risk_level TEXT,
            reason TEXT,
            status TEXT DEFAULT 'PENDING',
            edited_body TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def insert_audit_log(
    message_id: str,
    thread_id: str,
    classification: str,
    confidence: float,
    planner_decision: str,
    risk_level: str,
    action: str,
    approval_status: str,
    send_status: str,
    reason: str
):
    """Inserts a structured audit log entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (
            message_id, thread_id, classification, confidence, planner_decision,
            risk_level, action, approval_status, send_status, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        message_id, thread_id, classification, confidence, planner_decision,
        risk_level, action, approval_status, send_status, reason
    ))
    conn.commit()
    conn.close()


def save_processed_email(record: Dict[str, Any]) -> int:
    """Saves or updates a processed email in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO processed_emails (
            message_id, thread_id, sender, recipient, subject, body_clean,
            category, intent, priority, confidence, planner_decision, risk_level,
            final_action, approved, response_subject, response_body, reasoning_summary,
            processing_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record.get("message_id"),
        record.get("thread_id"),
        record.get("sender"),
        record.get("recipient"),
        record.get("subject"),
        record.get("body_clean"),
        record.get("category"),
        record.get("intent"),
        record.get("priority"),
        record.get("confidence", 0.0),
        record.get("planner_decision"),
        record.get("risk_level"),
        record.get("final_action"),
        1 if record.get("approved") else 0,
        record.get("response_subject"),
        record.get("response_body"),
        record.get("reasoning_summary"),
        record.get("processing_time_ms", 0)
    ))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def add_to_approval_queue(item: Dict[str, Any]) -> int:
    """Adds a draft email to human review interface queue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO approval_queue (
            message_id, thread_id, sender, subject, original_body,
            retrieved_context, draft_subject, draft_body, planner_decision,
            risk_level, reason, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
    """, (
        item.get("message_id"),
        item.get("thread_id"),
        item.get("sender"),
        item.get("subject"),
        item.get("original_body"),
        item.get("retrieved_context", ""),
        item.get("draft_subject"),
        item.get("draft_body"),
        item.get("planner_decision"),
        item.get("risk_level"),
        item.get("reason")
    ))
    queue_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return queue_id


def get_approval_queue(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns items from human approval queue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM approval_queue WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor.execute("SELECT * FROM approval_queue ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_approval_status(message_id: str, status: str, edited_body: Optional[str] = None) -> bool:
    """Updates approval status (APPROVED, REJECTED, EDITED)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    if edited_body:
        cursor.execute("""
            UPDATE approval_queue
            SET status = ?, edited_body = ?, updated_at = ?
            WHERE message_id = ?
        """, (status, edited_body, now, message_id))
    else:
        cursor.execute("""
            UPDATE approval_queue
            SET status = ?, updated_at = ?
            WHERE message_id = ?
        """, (status, now, message_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected


def get_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves recent audit logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_processed_emails(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves recent processed emails."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processed_emails ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_system_stats() -> Dict[str, Any]:
    """Computes real-time statistics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM processed_emails")
    total_processed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE final_action = 'AUTO_REPLY'")
    auto_replies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE planner_decision = 'HUMAN_APPROVAL' OR final_action = 'HUMAN_APPROVAL'")
    human_approvals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE planner_decision = 'CLARIFICATION_REQUIRED' OR final_action = 'CLARIFICATION_REQUIRED'")
    clarifications = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE planner_decision = 'TOOL_REQUIRED' OR final_action = 'TOOL_REQUIRED'")
    tool_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE planner_decision = 'IGNORE' OR final_action = 'IGNORE'")
    ignored_emails = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM processed_emails WHERE risk_level = 'HIGH'")
    high_risk_emails = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(processing_time_ms) FROM processed_emails WHERE processing_time_ms > 0")
    avg_row = cursor.fetchone()[0]
    avg_processing_time = round(avg_row, 1) if avg_row else 0.0

    conn.close()

    return {
        "total_emails_processed": total_processed,
        "auto_replies": auto_replies,
        "human_approvals": human_approvals,
        "clarification_requests": clarifications,
        "tool_required_cases": tool_cases,
        "ignored_emails": ignored_emails,
        "high_risk_emails": high_risk_emails,
        "avg_processing_time_ms": avg_processing_time
    }
