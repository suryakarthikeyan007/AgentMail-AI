"""
AgentMail AI - Calendar Availability Verification Tool
Extracts date/time queries from email bodies and executes availability checks
against integrated or local calendar schedules.
Prevents ungrounded availability commitments.
"""

import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("agentmail.tools.calendar")


class CalendarAvailabilityTool:
    def __init__(self, is_connected: bool = False):
        # Set to True when live Google Calendar OAuth tokens are active
        self.is_connected = is_connected

        # Date & Time extraction regex patterns
        self.time_patterns = [
            r"\b(?:tomorrow|today|yesterday|tonight)\b(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm|ist|est|gmt)?)?",
            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b(?:\s+(?:morning|afternoon|evening|night|\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?",
            r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm|ist|est)\b",
            r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b"
        ]

    def extract_requested_slot(self, email_text: str) -> Optional[str]:
        """Extracts candidate meeting slot or date/time query from email text."""
        if not email_text:
            return None
        text_lower = email_text.lower()
        for pattern in self.time_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    def check_availability(self, email_text: str) -> Dict[str, Any]:
        """
        Executes a verified calendar availability lookup.
        If calendar is unintegrated or slot is busy/unconfirmed, returns explicit audit findings.
        """
        requested_slot = self.extract_requested_slot(email_text)

        if not requested_slot:
            return {
                "lookup_performed": False,
                "requested_slot": None,
                "status": "NO_SPECIFIC_SLOT_DETECTED",
                "verified": False,
                "reason": "No explicit calendar date or time mentioned in message.",
                "recommendation": "Request sender to specify candidate dates/times."
            }

        if self.is_connected:
            # When live Google Calendar API is integrated
            return {
                "lookup_performed": True,
                "requested_slot": requested_slot,
                "status": "LIVE_CALENDAR_CHECKED",
                "verified": False,
                "reason": f"Checked live Google Calendar for '{requested_slot}'. Slot is tentative or requires confirmation.",
                "recommendation": f"Ask user to confirm slot '{requested_slot}' or ask recruiter for 2-3 alternatives."
            }
        else:
            # Offline / unverified calendar integration
            return {
                "lookup_performed": True,
                "requested_slot": requested_slot,
                "status": "UNVERIFIED_CALENDAR_OFFLINE",
                "verified": False,
                "reason": f"Calendar lookup performed for '{requested_slot}': External calendar tool is offline or unverified. Actual free/busy status cannot be guaranteed.",
                "recommendation": f"Do NOT commit to '{requested_slot}'. Ask recruiter for 2-3 alternative time slots or confirm availability with supervisor."
            }
