"""
AgentMail AI - Email Writer Agent
Generates professional, factual, context-grounded email responses using Llama 3.1.
Enforces tone standards and zero-hallucination policies based on RAG and conversation memory.
"""

from typing import Dict, Any
import logging
from backend.agents.base import BaseAgent

logger = logging.getLogger("agentmail.writer")

WRITER_SYSTEM_PROMPT = """You are the Email Writer Agent for AgentMail AI.
Your role is to craft polite, concise, professional, and factually grounded email responses on behalf of Pradeep Kumar A. (Final-Year B.Tech Student in AI & DS).

Strict Guidelines:
1. GROUNDED FACTS: ONLY make claims or share facts that exist in the RETRIEVED RAG CONTEXT or CONVERSATION MEMORY. When discussing education, skills, or projects, explicitly cite authentic details (e.g., CGPA 8.85, Department of AI & DS, Anna University, CogniFlow Systems internship, or AgentMail AI project).
2. CONVERSATION CONTINUITY: If the CONVERSATION THREAD CONTEXT contains prior turns, explicitly acknowledge the prior exchange (e.g., 'Following up on our earlier discussion regarding...'). Maintain conversation continuity across turns.
3. CALENDAR VERIFICATION: When the sender asks for meeting/interview slots and calendar availability is unconfirmed, explicitly state that you checked your calendar schedule and that the requested slot is currently unverified, then politely ask for 2-3 alternative time slots. NEVER invent availability.
4. SALARY POLICY: NEVER negotiate, promise, or accept salary figures autonomously.
5. If drafting a CLARIFICATION email, politely ask the sender for the specific missing details needed.
6. If drafting a response requiring HUMAN_APPROVAL, draft a proposed professional draft for the human to review.
7. Tone: Warm, professional, articulate, and respectful.
8. Always conclude with:
   Best regards,
   Pradeep Kumar A.
   B.Tech Artificial Intelligence & Data Science

Output Format:
You MUST respond with STRICT JSON ONLY:
{
  "subject": "<Re: Original Subject or appropriate response subject>",
  "body": "<Full text of the email response, properly formatted with paragraphs and salutation>",
  "reasoning_summary": "<1-2 sentence explanation of why this draft satisfies the prompt safely>"
}
"""


class EmailWriterAgent(BaseAgent):
    def draft_response(
        self,
        email_data: Dict[str, Any],
        classification: Dict[str, Any],
        planner_decision: Dict[str, Any],
        rag_context: str,
        memory_context: str
    ) -> Dict[str, Any]:
        """Drafts the email response based on planner decision, RAG context, and thread history."""
        decision = planner_decision.get("decision", "AUTO_REPLY")
        reason = planner_decision.get("reason", "")
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")

        prompt = f"""DRAFT EMAIL RESPONSE:
Original Email:
Sender: {sender}
Subject: {subject}
Body:
\"\"\"
{email_data.get('body')}
\"\"\"

Planner Directive:
Decision: {decision}
Reason: {reason}
Recommended Action: {planner_decision.get('recommended_action')}

Grounding Knowledge (RAG):
\"\"\"
{rag_context}
\"\"\"

Conversation Thread Context:
\"\"\"
{memory_context}
\"\"\"

Instructions:
Draft a complete, courteous, and accurate reply adhering strictly to the above facts.
Return STRICT JSON ONLY."""

        raw_response = self.call_llm(prompt=prompt, system_prompt=WRITER_SYSTEM_PROMPT, temperature=0.3)
        parsed = self.clean_json_response(raw_response)

        default_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        if not parsed or "body" not in parsed:
            # Fallback safe draft
            body = (
                f"Dear {sender.split('<')[0].strip()},\n\n"
                f"Thank you for contacting me regarding '{subject}'. I have received your message and am reviewing the details.\n\n"
                f"I will follow up with you shortly.\n\n"
                "Best regards,\nPradeep Kumar A.\nB.Tech Artificial Intelligence & Data Science"
            )
            return {
                "subject": default_subject,
                "body": body,
                "reasoning_summary": "Generated standard professional acknowledgement due to draft parsing fallback."
            }

        return {
            "subject": parsed.get("subject", default_subject),
            "body": parsed.get("body", "").strip(),
            "reasoning_summary": parsed.get("reasoning_summary", "Professional response grounded in knowledge base.")
        }
