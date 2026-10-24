"""
AgentMail AI - Email Preprocessor
Cleans, normalizes, and sanitizes incoming email payloads.
Removes signatures, quoted reply threads, HTML tags, tracking pixels, and whitespace noise.
"""

import re
import html
from datetime import datetime
from typing import Dict, Any, List, Optional


class EmailPreprocessor:
    def __init__(self):
        # Common email signature demarcation patterns
        self.signature_patterns = [
            r"\n\s*--\s*\n.*$",
            r"\n\s*__+\s*\n.*$",
            r"\n\s*(?:Best regards|Warm regards|Regards|Thanks and regards|Yours sincerely|Sincerely|Cheers)[\s,].*$",
            r"\n\s*Sent from my iPhone.*$",
            r"\n\s*Sent from my Android.*$",
            r"\n\s*Get Outlook for .*$"
        ]

        # Quoted reply markers (e.g. On Oct 5, 2026, John Doe wrote:)
        self.quote_patterns = [
            r"\n\s*On\s+.*?(?:wrote|sent):[\s\S]*$",
            r"\n\s*From:\s+.*?\nSent:\s+.*?\nTo:\s+.*?\nSubject:\s+.*$",
            r"\n\s*[-]+ Forwarded message [-]+[\s\S]*$",
            r"\n\s*>+[\s\S]*$"
        ]

    def strip_html_tags(self, raw_html: str) -> str:
        """Strips HTML formatting and decodes entities, preserving email address brackets."""
        if not raw_html:
            return ""
        # Remove script and style tags completely
        text = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", "", raw_html, flags=re.IGNORECASE)
        # Convert <br>, <p>, <div> to newlines
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</?(p|div|tr|li)[^>]*>", "\n", text, flags=re.IGNORECASE)
        # Strip all other HTML tags except angle brackets enclosing email addresses
        text = re.sub(r"<(?!/?[\w\.-]+@)[\w/][^>]*>", "", text)
        # Unescape HTML entities (&nbsp;, &amp;, etc.)
        text = html.unescape(text)
        return text

    def clean_body_text(self, body: str) -> str:
        """Removes signatures, excessive quotes, and normalizes spacing."""
        if not body:
            return ""

        # First decode HTML if present
        text = self.strip_html_tags(body)

        # Remove quoted reply history (using DOTALL to consume until end of string)
        for q_pat in self.quote_patterns:
            text = re.split(q_pat, text, flags=re.IGNORECASE | re.DOTALL)[0]

        # Remove email signatures
        for s_pat in self.signature_patterns:
            text = re.split(s_pat, text, flags=re.IGNORECASE | re.DOTALL)[0]

        # Normalize line endings and whitespace
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse 3 or more consecutive newlines into 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip trailing and leading whitespace
        text = text.strip()

        return text

    def process(self, raw_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms raw email input into a clean, normalized, structured dictionary.
        """
        raw_body = raw_email.get("body", "") or raw_email.get("text", "") or raw_email.get("snippet", "")
        cleaned_body = self.clean_body_text(raw_body)

        message_id = raw_email.get("message_id") or raw_email.get("id") or f"msg_{int(datetime.now().timestamp()*1000)}"
        thread_id = raw_email.get("thread_id") or raw_email.get("threadId") or message_id

        sender = raw_email.get("sender") or raw_email.get("from") or "unknown@domain.com"
        recipient = raw_email.get("recipient") or raw_email.get("to") or "pradeep.ai.engineer@example.com"
        subject = raw_email.get("subject") or "No Subject"

        timestamp = raw_email.get("timestamp") or datetime.now().isoformat()
        attachments = raw_email.get("attachments", [])

        return {
            "message_id": str(message_id),
            "thread_id": str(thread_id),
            "sender": str(sender).strip(),
            "recipient": str(recipient).strip(),
            "subject": str(subject).strip(),
            "body": cleaned_body,
            "raw_body": raw_body,
            "timestamp": timestamp,
            "attachments": attachments
        }
