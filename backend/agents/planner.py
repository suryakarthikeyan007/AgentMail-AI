"""
AgentMail AI - Planner Agent
The core agentic brain of the system.
Evaluates the email, classification, retrieved RAG context, conversation memory,
and strict safety rules to determine the next deterministic action.
"""

from typing import Dict, Any, List
import logging
from backend.agents.base import BaseAgent

logger = logging.getLogger("agentmail.planner")

PLANNER_SYSTEM_PROMPT = """You are the Lead Planner Agent for AgentMail AI.
Your purpose is to determine WHAT SHOULD HAPPEN NEXT for an incoming email.
Unlike a passive chatbot that blindly drafts text, you act as an executive decision gatekeeper.

You MUST choose exactly ONE of the following 5 decisions:
1. "AUTO_REPLY": The request is routine, safe, factual, and 100% supported by the retrieved knowledge base. No unverified commitments are made.
2. "HUMAN_APPROVAL": The email involves sensitive matters (salary, legal, offers, contracts), high risks, requires commitments (like specific calendar interview times when calendar is unverified), or requires user verification.
3. "CLARIFICATION_REQUIRED": The sender's request is ambiguous, lacks essential parameters, or asks for specifics not present in the thread or knowledge base.
4. "TOOL_REQUIRED": The email requires an external service or tool (such as checking a calendar, triggering a workflow, querying an external database) that is defined and available.
5. "IGNORE": The email is promotional spam, cold sales pitch, marketing newsletter, or unsolicited noise. No reply is needed.

CRITICAL SAFETY & COMMITMENT RULES (ZERO HALLUCINATION):
- NEVER invent meeting dates, interview availability, or time slots. If an email asks "Can we schedule an interview tomorrow?", and no verified calendar tool is present, you MUST decide HUMAN_APPROVAL or CLARIFICATION_REQUIRED. NEVER AUTO_REPLY with a fake commitment.
- Any email mentioning salary negotiation, compensation figures (e.g., "₹12 LPA"), contract signing, or legal matters MUST be routed to HUMAN_APPROVAL.
- If classification is "Spam/Low Value", you MUST choose IGNORE.
- If the sender asks for resume/skills and that information exists in the retrieved RAG context, and no calendar commitment is required, AUTO_REPLY is permitted.

Output Format:
You MUST respond with STRICT JSON ONLY. Schema:
{
  "decision": "AUTO_REPLY | HUMAN_APPROVAL | CLARIFICATION_REQUIRED | TOOL_REQUIRED | IGNORE",
  "reason": "<Detailed explanation of why this decision was made and what safety rules triggered it>",
  "confidence": <float between 0.0 and 1.0>,
  "required_information": ["<info1>", "<info2>"],
  "recommended_action": "<Clear 1-sentence directive for the system or user>"
}
"""


class PlannerAgent(BaseAgent):
    def plan(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        rag_context: str,
        memory_context: str,
        available_tools: List[str] = None
    ) -> Dict[str, Any]:
        """
        Executes reasoning to decide the next action.
        Evaluates safety rules first, prompts the LLM, and enforces safety overrides.
        """
        tools_list = available_tools or ["calendar_check_tool (status: offline)"]
        tools_str = ", ".join(tools_list)

        # Execute active calendar availability check
        from backend.tools.calendar_tool import CalendarAvailabilityTool
        cal_tool = CalendarAvailabilityTool()
        calendar_audit = cal_tool.check_availability(email_data.get("body", "") + " " + email_data.get("subject", ""))

        prompt = f"""EVALUATE THE INCOMING EMAIL:
From: {email_data.get('sender')}
Subject: {email_data.get('subject')}
Clean Body:
\"\"\"
{email_data.get('body')}
\"\"\"

CLASSIFIER FINDINGS:
Category: {classification.get('category')}
Intent: {classification.get('intent')}
Priority: {classification.get('priority')}
Sensitivity: {classification.get('sensitivity')}
Requested Action: {classification.get('requested_action')}

CALENDAR AVAILABILITY CHECK:
Lookup Performed: {calendar_audit.get('lookup_performed')}
Requested Slot: {calendar_audit.get('requested_slot')}
Calendar Status: {calendar_audit.get('status')}
Findings: {calendar_audit.get('reason')}

RETRIEVED RAG CONTEXT:
\"\"\"
{rag_context}
\"\"\"

CONVERSATION THREAD MEMORY:
\"\"\"
{memory_context}
\"\"\"

AVAILABLE EXTERNAL TOOLS:
{tools_str}

Analyze the requirements, check for calendar/salary/legal safety risks, and produce the STRICT JSON decision."""

        raw_response = self.call_llm(prompt=prompt, system_prompt=PLANNER_SYSTEM_PROMPT, temperature=0.1)
        parsed = self.clean_json_response(raw_response)

        decision = parsed.get("decision", "")
        valid_decisions = {"AUTO_REPLY", "HUMAN_APPROVAL", "CLARIFICATION_REQUIRED", "TOOL_REQUIRED", "IGNORE"}

        # Deterministic Safety Gate Overrides
        category = classification.get("category", "")
        body_lower = email_data.get("body", "").lower()
        subject_lower = email_data.get("subject", "").lower()

        # Risk severity classification (distinct from approval requirement)
        risk_severity = "LOW"

        # Rule 1: Spam -> IGNORE
        if category == "Spam/Low Value" or any(w in body_lower for w in ["win a free", "lottery", "unsolicited marketing"]):
            decision = "IGNORE"
            risk_severity = "LOW"
            reason = "Spam or promotional message detected; ignoring to conserve resources and avoid engagement."

        # Rule 2: Salary / Legal / Contract -> HUMAN_APPROVAL with HIGH risk
        elif category == "Sensitive" or any(w in body_lower for w in ["salary", "lpa", "ctc", "per annum", "legal notice", "confidentiality agreement"]):
            decision = "HUMAN_APPROVAL"
            risk_severity = "HIGH"
            reason = parsed.get("reason") or "APPROVAL REQUIRED: Contains sensitive financial, salary, or legal topics. Risk Severity: HIGH."

        # Rule 3: Scheduling / Interview / Meeting without verified calendar tool -> HUMAN_APPROVAL with MEDIUM risk
        elif any(w in body_lower or w in subject_lower for w in ["schedule an interview", "interview tomorrow", "schedule a meeting", "meet tomorrow", "time slot", "are you free at"]) or calendar_audit.get("lookup_performed"):
            decision = "HUMAN_APPROVAL"
            risk_severity = "MEDIUM"
            slot_name = calendar_audit.get("requested_slot") or "requested time"
            reason = f"APPROVAL REQUIRED: Interview/Meeting scheduling requested for '{slot_name}'. Calendar lookup: {calendar_audit.get('status')}. Risk Severity: MEDIUM due to schedule commitment conflict exposure."

        # Fallback validation
        if decision not in valid_decisions:
            decision = "HUMAN_APPROVAL"
            risk_severity = "MEDIUM"
            reason = "APPROVAL REQUIRED: Planner generated unverified decision state; routing to human review for safety."

        return {
            "decision": decision,
            "risk_severity": risk_severity,
            "reason": reason,
            "confidence": float(parsed.get("confidence", 0.92)),
            "required_information": parsed.get("required_information", []),
            "recommended_action": parsed.get("recommended_action", f"Proceed with {decision}"),
            "calendar_audit": calendar_audit
        }
