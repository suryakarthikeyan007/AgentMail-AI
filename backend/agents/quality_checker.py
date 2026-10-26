"""
AgentMail AI - Quality & Risk Checker Agent
Independent critic agent that evaluates draft emails for factual hallucinations,
risky calendar/salary commitments, tone appropriateness, privacy leaks, and grammatical quality.
"""

from typing import Dict, Any, List
import logging
from backend.agents.base import BaseAgent

logger = logging.getLogger("agentmail.quality_checker")

QUALITY_CHECKER_SYSTEM_PROMPT = """You are the Quality & Risk Checker Agent for AgentMail AI.
You are an independent safety critic and verification engine.
Your mission is to audit draft email responses BEFORE they are transmitted.

Audit Checklist:
1. Factual Consistency & Hallucination: Are any facts invented that are not present in the RAG Context?
2. Risky Commitments: Did the draft promise a specific meeting date/time, interview availability, or salary commitment without explicit prior authorization? (IF YES -> Risk MUST be HIGH).
3. Tone & Professionalism: Is the language polite, formal, and free from offensive or inappropriate phrasing?
4. Privacy & Leakage: Are any private keys, passwords, or personal confidential data leaked?
5. Relevance: Does the response directly address the sender's inquiry?

Risk Level Definitions:
- "LOW": Completely grounded in context, zero unauthorized commitments, polite and professional.
- "MEDIUM": Minor tone or phrasing ambiguities that do not cause financial, legal, or calendar harm.
- "HIGH": Contains unverified availability commitments ("Sure, tomorrow at 3 PM works"), salary figures, legal agreements, or ungrounded claims. MUST NOT BE SENT AUTOMATICALLY.

Output Format:
Return STRICT JSON ONLY:
{
  "approved": true | false,
  "risk_level": "LOW | MEDIUM | HIGH",
  "issues": ["<issue 1>", "<issue 2>"],
  "corrections": ["<suggested correction 1>"],
  "reason": "<Detailed audit conclusion>"
}
"""


class QualityRiskCheckerAgent(BaseAgent):
    def audit(
        self,
        draft_response: Dict[str, Any],
        original_email: Dict[str, Any],
        rag_context: str,
        memory_context: str,
        planner_decision: str
    ) -> Dict[str, Any]:
        """
        Conducts an adversarial risk audit of the proposed draft.
        Enforces deterministic hard rules alongside LLM verification.
        """
        draft_body = draft_response.get("body", "")
        draft_subject = draft_response.get("subject", "")

        prompt = f"""AUDIT THIS PROPOSED EMAIL RESPONSE:
Original Email Body:
\"\"\"
{original_email.get('body')}
\"\"\"

Proposed Draft Subject: {draft_subject}
Proposed Draft Body:
\"\"\"
{draft_body}
\"\"\"

Reference RAG Context:
\"\"\"
{rag_context}
\"\"\"

Conversation Thread Context:
\"\"\"
{memory_context}
\"\"\"

Planner Intended Decision: {planner_decision}

Check for hallucinations, unauthorized commitments (dates, times, money), and tone flaws.
Return STRICT JSON ONLY."""

        raw_response = self.call_llm(prompt=prompt, system_prompt=QUALITY_CHECKER_SYSTEM_PROMPT, temperature=0.1)
        parsed = self.clean_json_response(raw_response)

        # Deterministic Safety Overrides
        body_lower = draft_body.lower()
        hard_issues = []
        is_high_risk = False
        is_medium_risk = False

        # Check for ungrounded interview/meeting commitments
        risky_commit_words = ["i will be available tomorrow", "tomorrow at", "tomorrow works", "i can meet you at", "let us meet tomorrow", "i confirm tomorrow"]
        for rw in risky_commit_words:
            if rw in body_lower:
                hard_issues.append(f"Contains unverified calendar commitment: '{rw}'")
                is_high_risk = True

        # Check for salary mentions
        if any(w in body_lower for w in ["lpa", "ctc", "salary of", "per annum", "compensation package"]):
            hard_issues.append("Contains sensitive salary or compensation terms.")
            is_high_risk = True

        # Check if planner required human approval due to unverified scheduling exposure
        if planner_decision == "HUMAN_APPROVAL" and not is_high_risk:
            is_medium_risk = True
            hard_issues.append("Pending supervisor review to prevent unverified calendar schedule conflicts.")

        if is_high_risk:
            risk_level = "HIGH"
            approved = False
        elif is_medium_risk or parsed.get("risk_level") == "MEDIUM":
            risk_level = "MEDIUM"
            approved = False # Requires human supervisor sign-off before dispatch
        else:
            risk_level = "LOW"
            approved = bool(parsed.get("approved", True))

        combined_issues = list(set(parsed.get("issues", []) + hard_issues))

        return {
            "approved": approved,
            "risk_level": risk_level,
            "issues": combined_issues,
            "corrections": parsed.get("corrections", []),
            "reason": parsed.get("reason", f"Risk severity: {risk_level}. Approval required: {not approved}.")
        }
