"""
AgentMail AI - Persistent Conversation Memory
Manages stateful conversation context linked by Gmail thread ID.
Persists across executions in SQLite database.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import sqlite3

from backend.config import DATABASE_PATH

logger = logging.getLogger("agentmail.memory")


class ConversationMemoryManager:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_thread_memory(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves summarized conversation memory for a Gmail thread."""
        if not thread_id:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversation_memory WHERE thread_id = ?", (thread_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        data = dict(row)
        try:
            data["key_facts"] = json.loads(data["key_facts"]) if data["key_facts"] else []
        except Exception:
            data["key_facts"] = []

        try:
            data["message_history"] = json.loads(data["message_history"]) if data["message_history"] else []
        except Exception:
            data["message_history"] = []

        return data

    def update_thread_memory(
        self,
        thread_id: str,
        sender: str,
        subject: str,
        incoming_message: str,
        category: str,
        planner_decision: str,
        response_summary: str,
        extracted_facts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Updates thread memory after an incoming email is analyzed and actioned.
        Appends message history, updates key facts, and creates a concise conversation summary.
        """
        if not thread_id:
            return {}

        existing = self.get_thread_memory(thread_id)
        now_str = datetime.now().isoformat()

        if existing:
            history = existing.get("message_history", [])
            existing_facts = existing.get("key_facts", [])
            new_facts = list(set(existing_facts + (extracted_facts or [])))
            turn_number = len(history) + 1

            new_turn = {
                "turn": turn_number,
                "timestamp": now_str,
                "sender": sender,
                "incoming_snippet": (incoming_message[:150] + "...") if len(incoming_message) > 150 else incoming_message,
                "category": category,
                "planner_decision": planner_decision,
                "response_summary": response_summary
            }
            history.append(new_turn)

            summary = f"Thread with {sender} on '{subject}'. {len(history)} interaction(s). Last decision: {planner_decision}. Topics: {', '.join(new_facts[:5]) if new_facts else category}."

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversation_memory
                SET sender = ?, subject = ?, summary = ?, key_facts = ?,
                    last_classification = ?, last_decision = ?, message_history = ?, updated_at = ?
                WHERE thread_id = ?
            """, (
                sender,
                subject,
                summary,
                json.dumps(new_facts),
                category,
                planner_decision,
                json.dumps(history[-10:]), # Keep last 10 turns for memory efficiency
                now_str,
                thread_id
            ))
            conn.commit()
            conn.close()

            return {
                "thread_id": thread_id,
                "turn_count": len(history),
                "summary": summary,
                "key_facts": new_facts,
                "is_existing_conversation": True
            }
        else:
            initial_facts = extracted_facts or [category]
            initial_history = [{
                "turn": 1,
                "timestamp": now_str,
                "sender": sender,
                "incoming_snippet": (incoming_message[:150] + "...") if len(incoming_message) > 150 else incoming_message,
                "category": category,
                "planner_decision": planner_decision,
                "response_summary": response_summary
            }]
            summary = f"Started conversation with {sender} regarding '{subject}'. Classified as {category}."

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_memory (
                    thread_id, sender, subject, summary, key_facts,
                    last_classification, last_decision, message_history, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                thread_id,
                sender,
                subject,
                summary,
                json.dumps(initial_facts),
                category,
                planner_decision,
                json.dumps(initial_history),
                now_str
            ))
            conn.commit()
            conn.close()

            return {
                "thread_id": thread_id,
                "turn_count": 1,
                "summary": summary,
                "key_facts": initial_facts,
                "is_existing_conversation": False
            }

    def format_memory_for_prompt(self, thread_id: str) -> str:
        """Formats conversation memory for LLM prompt context."""
        mem = self.get_thread_memory(thread_id)
        if not mem:
            return "No previous conversation history found for this thread (New conversation)."

        history_lines = []
        for item in mem.get("message_history", []):
            history_lines.append(
                f"- Turn {item.get('turn')}: From {item.get('sender')} -> Decided: {item.get('planner_decision')}. "
                f"Snippet: \"{item.get('incoming_snippet')}\". Reply summary: \"{item.get('response_summary')}\""
            )

        facts_str = ", ".join(mem.get("key_facts", [])) if mem.get("key_facts") else "None"

        return (
            f"Previous Conversation Context for Thread [{thread_id}]:\n"
            f"Summary: {mem.get('summary')}\n"
            f"Known Facts: {facts_str}\n"
            f"History:\n" + "\n".join(history_lines)
        )
