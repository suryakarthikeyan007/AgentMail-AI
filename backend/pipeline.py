"""
AgentMail AI - End-to-End Agentic Pipeline Orchestrator
Coordinates:
CLASSIFY → RETRIEVE → REMEMBER → PLAN → DECIDE → ACT → VERIFY → REMEMBER
"""

import time
import logging
from typing import Dict, Any, Optional

from backend.agents.preprocessor import EmailPreprocessor
from backend.agents.classifier import EmailClassifierAgent
from backend.agents.planner import PlannerAgent
from backend.agents.writer import EmailWriterAgent
from backend.agents.quality_checker import QualityRiskCheckerAgent
from backend.rag.retriever import RAGRetriever
from backend.memory.conversation_memory import ConversationMemoryManager
from backend.safety.safety_gate import SafetyGate
from backend.database.db import (
    save_processed_email,
    insert_audit_log,
    add_to_approval_queue
)

logger = logging.getLogger("agentmail.pipeline")


class EmailAgentPipeline:
    def __init__(self):
        self.preprocessor = EmailPreprocessor()
        self.classifier = EmailClassifierAgent()
        self.retriever = RAGRetriever()
        self.memory = ConversationMemoryManager()
        self.planner = PlannerAgent()
        self.writer = EmailWriterAgent()
        self.quality_checker = QualityRiskCheckerAgent()
        self.safety_gate = SafetyGate()

    def process_email(self, raw_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the complete Agentic AI lifecycle for an incoming email.
        """
        start_time = time.time()
        pipeline_trace = []

        # STEP 1: Preprocessing
        preprocessed = self.preprocessor.process(raw_email)
        message_id = preprocessed["message_id"]
        thread_id = preprocessed["thread_id"]
        sender = preprocessed["sender"]
        subject = preprocessed["subject"]
        body = preprocessed["body"]

        pipeline_trace.append({
            "step": "PREPROCESS",
            "status": "COMPLETED",
            "details": f"Cleaned body ({len(body)} chars), sender: {sender}, thread_id: {thread_id}"
        })

        # STEP 2: Classification (Llama 3.1)
        classification = self.classifier.classify(preprocessed)
        pipeline_trace.append({
            "step": "CLASSIFY",
            "status": "COMPLETED",
            "category": classification.get("category"),
            "priority": classification.get("priority"),
            "confidence": classification.get("confidence"),
            "intent": classification.get("intent")
        })

        # STEP 3: RAG Knowledge Retrieval (nomic-embed-text)
        query_text = f"{subject} {body[:250]}"
        rag_result = self.retriever.retrieve_context(query_text, top_k=2)
        rag_context = rag_result.get("formatted_text", "")
        pipeline_trace.append({
            "step": "RETRIEVE_RAG",
            "status": "COMPLETED",
            "sources": rag_result.get("sources", []),
            "chunk_count": len(rag_result.get("chunks", []))
        })

        # STEP 4: Conversation Memory Retrieval
        memory_context = self.memory.format_memory_for_prompt(thread_id)
        existing_thread = self.memory.get_thread_memory(thread_id)
        pipeline_trace.append({
            "step": "RETRIEVE_MEMORY",
            "status": "COMPLETED",
            "is_thread_existing": existing_thread is not None,
            "turn_history_count": len(existing_thread.get("message_history", [])) if existing_thread else 0
        })

        # STEP 5: Planner Agent Reasoning
        planner_result = self.planner.plan(
            email_data=preprocessed,
            classification=classification,
            rag_context=rag_context,
            memory_context=memory_context
        )
        planner_decision = planner_result.get("decision", "HUMAN_APPROVAL")
        pipeline_trace.append({
            "step": "PLAN",
            "status": "COMPLETED",
            "decision": planner_decision,
            "reason": planner_result.get("reason"),
            "confidence": planner_result.get("confidence")
        })

        # STEP 6: Handling by Planner Decision
        draft_response = {"subject": f"Re: {subject}", "body": "", "reasoning_summary": ""}
        quality_audit = {"approved": True, "risk_level": "LOW", "issues": [], "reason": "No draft required"}
        dispatch_result = None

        if planner_decision == "IGNORE":
            final_action = "IGNORE"
            action_reason = "Ignored promotional/low-value message as determined by Planner."
            response_summary = "Email ignored (no reply sent)."

        elif planner_decision == "TOOL_REQUIRED":
            final_action = "TOOL_REQUIRED"
            action_reason = "Awaiting authorized external tool integration."
            response_summary = f"Flagged tool requirement: {', '.join(planner_result.get('required_information', ['Calendar Tool']))}"

        else:
            # Decisions: AUTO_REPLY, HUMAN_APPROVAL, CLARIFICATION_REQUIRED
            # STEP 7: Draft Generation (Email Writer Agent)
            draft_response = self.writer.draft_response(
                email_data=preprocessed,
                classification=classification,
                planner_decision=planner_result,
                rag_context=rag_context,
                memory_context=memory_context
            )
            pipeline_trace.append({
                "step": "WRITE_DRAFT",
                "status": "COMPLETED",
                "draft_subject": draft_response.get("subject"),
                "snippet": draft_response.get("body", "")[:120] + "..."
            })

            # STEP 8: Quality & Risk Checker Audit
            quality_audit = self.quality_checker.audit(
                draft_response=draft_response,
                original_email=preprocessed,
                rag_context=rag_context,
                memory_context=memory_context,
                planner_decision=planner_decision
            )
            pipeline_trace.append({
                "step": "QUALITY_AUDIT",
                "status": "COMPLETED",
                "risk_level": quality_audit.get("risk_level"),
                "audit_approved": quality_audit.get("approved"),
                "issues": quality_audit.get("issues")
            })

            # STEP 9: Safety Gate Routing Evaluation
            final_action, action_reason = self.safety_gate.evaluate_routing(planner_result, quality_audit)

            # STEP 10: Execution / Dispatch
            if final_action in ["AUTO_REPLY", "CLARIFICATION_REQUIRED"]:
                dispatch_result = self.safety_gate.dispatch_email(
                    recipient=sender,
                    subject=draft_response.get("subject"),
                    body=draft_response.get("body"),
                    thread_id=thread_id
                )
                pipeline_trace.append({
                    "step": "DISPATCH",
                    "status": "COMPLETED",
                    "dispatch_mode": dispatch_result.get("mode"),
                    "details": dispatch_result.get("message")
                })
                response_summary = f"Sent reply: {draft_response.get('subject')} ({dispatch_result.get('mode')})"
            else:
                # Routed to HUMAN_APPROVAL
                add_to_approval_queue({
                    "message_id": message_id,
                    "thread_id": thread_id,
                    "sender": sender,
                    "subject": subject,
                    "original_body": body,
                    "retrieved_context": rag_context,
                    "draft_subject": draft_response.get("subject"),
                    "draft_body": draft_response.get("body"),
                    "planner_decision": planner_decision,
                    "risk_level": quality_audit.get("risk_level"),
                    "reason": action_reason
                })
                pipeline_trace.append({
                    "step": "QUEUE_HUMAN_APPROVAL",
                    "status": "PENDING",
                    "reason": action_reason
                })
                response_summary = f"Held in Human Approval Queue. Reason: {action_reason}"

        # STEP 11: Persistent Conversation Memory Update
        mem_update = self.memory.update_thread_memory(
            thread_id=thread_id,
            sender=sender,
            subject=subject,
            incoming_message=body,
            category=classification.get("category"),
            planner_decision=planner_decision,
            response_summary=response_summary,
            extracted_facts=classification.get("entities", [])
        )
        pipeline_trace.append({
            "step": "UPDATE_MEMORY",
            "status": "COMPLETED",
            "turn_count": mem_update.get("turn_count", 1)
        })

        # Calculation of processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # STEP 12: Persistent Audit Log & Record Store
        record = {
            "message_id": message_id,
            "thread_id": thread_id,
            "sender": sender,
            "recipient": preprocessed["recipient"],
            "subject": subject,
            "body_clean": body,
            "category": classification.get("category"),
            "intent": classification.get("intent"),
            "priority": classification.get("priority"),
            "confidence": classification.get("confidence", 0.9),
            "planner_decision": planner_decision,
            "risk_level": quality_audit.get("risk_level"),
            "final_action": final_action,
            "approved": final_action == "AUTO_REPLY",
            "response_subject": draft_response.get("subject"),
            "response_body": draft_response.get("body"),
            "reasoning_summary": draft_response.get("reasoning_summary"),
            "processing_time_ms": processing_time_ms
        }
        save_processed_email(record)

        insert_audit_log(
            message_id=message_id,
            thread_id=thread_id,
            classification=classification.get("category"),
            confidence=classification.get("confidence", 0.9),
            planner_decision=planner_decision,
            risk_level=quality_audit.get("risk_level"),
            action=final_action,
            approval_status="APPROVED" if final_action == "AUTO_REPLY" else ("QUEUED" if final_action == "HUMAN_APPROVAL" else "N/A"),
            send_status="SIMULATED" if (dispatch_result and dispatch_result.get("mode") == "TEST_MODE_SIMULATION") else ("SENT" if dispatch_result else "NOT_SENT"),
            reason=action_reason
        )

        return {
            "message_id": message_id,
            "thread_id": thread_id,
            "sender": sender,
            "subject": subject,
            "classification": classification,
            "rag_context": rag_result,
            "conversation_memory": mem_update,
            "planner_decision": planner_result,
            "draft_response": draft_response,
            "quality_audit": quality_audit,
            "final_action": final_action,
            "action_reason": action_reason,
            "dispatch_result": dispatch_result,
            "processing_time_ms": processing_time_ms,
            "pipeline_trace": pipeline_trace
        }
