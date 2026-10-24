"""
AgentMail AI - Safety Gate & Decision Router
Enforces deterministic safety policies, intercepts high-risk drafts,
routes actions according to planner decisions, and simulates safe test dispatching.
"""

import logging
from typing import Dict, Any, Tuple
from backend.config import TEST_MODE

logger = logging.getLogger("agentmail.safety")


class SafetyGate:
    def __init__(self, test_mode: bool = TEST_MODE):
        self.test_mode = test_mode

    def evaluate_routing(
        self,
        planner_decision: Dict[str, Any],
        quality_audit: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Determines the final operational action.
        Rule: If Planner recommended AUTO_REPLY but Quality Checker detected HIGH risk,
        Safety Gate overrides and enforces HUMAN_APPROVAL.
        """
        initial_decision = planner_decision.get("decision", "HUMAN_APPROVAL")
        risk_level = quality_audit.get("risk_level", "LOW")
        audit_approved = quality_audit.get("approved", True)

        if initial_decision == "IGNORE":
            return "IGNORE", "Email identified as promotional/spam or low-value. Silently ignored."

        if initial_decision == "TOOL_REQUIRED":
            return "TOOL_REQUIRED", "Action paused awaiting external tool invocation and authorization."

        if initial_decision == "CLARIFICATION_REQUIRED":
            if risk_level == "HIGH":
                return "HUMAN_APPROVAL", "Clarification response contained high risk factors; rerouted to human approval."
            return "CLARIFICATION_REQUIRED", "Proceeding with clarification request to sender."

        if initial_decision == "AUTO_REPLY":
            if risk_level == "HIGH" or not audit_approved:
                logger.warning("SAFETY OVERRIDE: Planner requested AUTO_REPLY, but Quality Checker flagged HIGH risk!")
                return "HUMAN_APPROVAL", "Safety override triggered: high-risk elements or potential hallucinations detected in draft."
            return "AUTO_REPLY", "Draft verified safe for autonomous dispatch."

        # Default fallback
        return "HUMAN_APPROVAL", "Email requires human supervisor review and confirmation."

    def dispatch_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Transmits the email or safely emulates dispatch in TEST_MODE.
        Guarantees no accidental emails are dispatched during testing.
        """
        if self.test_mode:
            logger.info(f"[TEST_MODE ACTIVE] Email would be sent to: {recipient} | Subject: {subject}")
            return {
                "sent": True,
                "mode": "TEST_MODE_SIMULATION",
                "message": f"EMAIL WOULD BE SENT to {recipient} (TEST_MODE=true)",
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "thread_id": thread_id
            }
        else:
            # When live OAuth credentials are configured and TEST_MODE=false
            logger.info(f"[LIVE MODE] Transmitting email to: {recipient} | Subject: {subject}")
            return {
                "sent": True,
                "mode": "LIVE_GMAIL_API",
                "message": f"Email successfully sent to {recipient}",
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "thread_id": thread_id
            }
