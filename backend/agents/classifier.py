"""
AgentMail AI - Email Classifier Agent
Employs Llama 3.1 to classify incoming emails into structured categories, intents, priorities,
and sensitivity ratings with strict JSON output.
"""

from typing import Dict, Any, List
import logging
from backend.agents.base import BaseAgent

logger = logging.getLogger("agentmail.classifier")

CLASSIFIER_SYSTEM_PROMPT = """You are the Email Classifier Agent for AgentMail AI.
Your role is to rigorously classify incoming emails into exact categories, extract entities, identify intent, evaluate urgency, and assess sensitivity.

You MUST choose exactly ONE category from:
- Interview
- Meeting
- Job
- General
- Request
- Information
- Follow-up
- Spam/Low Value
- Sensitive

Classification Criteria:
- "Interview": Any invitation, interview round scheduling, coding assessment, technical interview, or viva discussion.
- "Meeting": Requests for synchronizing a call, discussion, sync up, or 1-on-1 meeting.
- "Job": Inquiries about job applications, job openings, interest confirmations, recruiters reaching out.
- "Request": Direct requests for documents (like resumes), credentials, portfolio links, or project explanations.
- "Follow-up": Inquiries following up on previous messages, updates on pending decisions, or check-ins.
- "Spam/Low Value": Marketing brochures, unsolicited pitches, bulk promotions, spam, scams, phishing.
- "Sensitive": Legal matters, salary negotiations, NDA discussions, contracts, confidential data, emotional disputes.
- "Information": Informational announcements, newsletters, status updates not requiring reply.
- "General": Polite greetings, general social inquiries not fitting above.

Output Format:
You MUST respond with STRICT JSON ONLY. Do not prepend or append markdown or commentary.
Required schema:
{
  "category": "Interview | Meeting | Job | General | Request | Information | Follow-up | Spam/Low Value | Sensitive",
  "intent": "<Concise 3-7 word description of intent>",
  "priority": "High | Medium | Low",
  "reply_required": true | false,
  "sensitivity": "High | Medium | Low",
  "confidence": <float between 0.0 and 1.0>,
  "urgency": "High | Medium | Low",
  "requested_action": "<Specific action requested by sender, or 'None'>",
  "entities": ["<entity1>", "<entity2>"]
}
"""


class EmailClassifierAgent(BaseAgent):
    def classify(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies the preprocessed email using Llama 3.1.
        Fallback to rule-based classification if model returns malformed JSON.
        """
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")
        body = self.sanitize_untrusted_input(email_data.get("body", ""))

        prompt = f"""Incoming Email:
From: {sender}
Subject: {subject}
Content:
\"\"\"
{body}
\"\"\"

Analyze this email and output the required STRICT JSON."""

        raw_response = self.call_llm(prompt=prompt, system_prompt=CLASSIFIER_SYSTEM_PROMPT, temperature=0.1)
        parsed = self.clean_json_response(raw_response)

        # Validate parsed attributes and provide robust schema defaults
        valid_categories = {
            "Interview", "Meeting", "Job", "General", "Request",
            "Information", "Follow-up", "Spam/Low Value", "Sensitive"
        }

        category = parsed.get("category", "")
        if category not in valid_categories:
            # Fallback heuristic if LLM hallucinated an invalid category
            subject_lower = subject.lower()
            body_lower = body.lower()
            if any(w in body_lower or w in subject_lower for w in ["salary", "lpa", "offer letter", "legal", "confidential"]):
                category = "Sensitive"
            elif any(w in body_lower or w in subject_lower for w in ["interview", "screening", "technical round"]):
                category = "Interview"
            elif any(w in body_lower or w in subject_lower for w in ["meeting", "schedule", "call tomorrow", "sync"]):
                category = "Meeting"
            elif any(w in body_lower or w in subject_lower for w in ["resume", "cv", "send your", "documents"]):
                category = "Request"
            elif any(w in body_lower or w in subject_lower for w in ["application", "role", "position", "interest"]):
                category = "Job"
            elif any(w in body_lower or w in subject_lower for w in ["following up", "follow up", "status update"]):
                category = "Follow-up"
            elif any(w in body_lower or w in subject_lower for w in ["viagra", "lottery", "crypto", "unsolicited", "discount"]):
                category = "Spam/Low Value"
            else:
                category = "General"

        result = {
            "category": category,
            "intent": parsed.get("intent", f"{category} related email"),
            "priority": parsed.get("priority", "Medium"),
            "reply_required": bool(parsed.get("reply_required", category not in ["Spam/Low Value", "Information"])),
            "sensitivity": parsed.get("sensitivity", "High" if category == "Sensitive" else "Low"),
            "confidence": float(parsed.get("confidence", 0.90)),
            "urgency": parsed.get("urgency", "Medium"),
            "requested_action": parsed.get("requested_action", "Review and respond"),
            "entities": parsed.get("entities", [])
        }
        return result
