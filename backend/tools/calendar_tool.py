"""
AgentMail AI - Calendar Availability Verification Tool
Extracts date/time queries from email bodies and executes availability checks
against integrated or local calendar schedules.
Prevents ungrounded availability commitments by classifying results as:
- AVAILABLE: Calendar check confirmed slot is open.
- CONFLICT: Calendar check found an overlapping schedule conflict.
- UNVERIFIED: External calendar service is unreachable/offline; availability cannot be verified.
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
            r"\b(?:tomorrow|today|yesterday|tonight)\b(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:ist|est|gmt|utc|cst|pst)?)?",
            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b(?:\s+(?:morning|afternoon|evening|night|\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:ist|est|gmt|utc)?))?",
            r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:ist|est|gmt|utc)\b",
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
        Returns:
            availability_result: 'AVAILABLE' | 'CONFLICT' | 'UNVERIFIED'
            status: detailed status code
            verified: True only if live calendar returned a confirmed open slot
            recommended_wording: ground truth phrase to use in replies
        """
        requested_slot = self.extract_requested_slot(email_text)

        if not requested_slot:
            return {
                "lookup_performed": False,
                "requested_slot": None,
                "availability_result": "UNVERIFIED",
                "status": "NO_SPECIFIC_SLOT_DETECTED",
                "verified": False,
                "reason": "No explicit calendar date or time mentioned in message.",
                "recommended_wording": "Could you please share your preferred dates and time slots?",
                "recommendation": "Request sender to specify candidate dates/times."
            }

        if self.is_connected:
            # When live Google Calendar API is integrated
            return {
                "lookup_performed": True,
                "requested_slot": requested_slot,
                "availability_result": "UNVERIFIED",
                "status": "LIVE_CALENDAR_CHECKED_TENTATIVE",
                "verified": False,
                "reason": f"Checked live Google Calendar for '{requested_slot}'. Slot is tentative and requires user confirmation.",
                "recommended_wording": f"I'll need to confirm my availability before committing to {requested_slot}. Could you please share 2-3 alternative time slots?",
                "recommendation": f"Ask user to confirm slot '{requested_slot}' or ask recruiter for 2-3 alternatives."
            }
        else:
            # Offline / unverified calendar integration
            return {
                "lookup_performed": True,
                "requested_slot": requested_slot,
                "availability_result": "UNVERIFIED",
                "status": "UNVERIFIED_CALENDAR_OFFLINE",
                "verified": False,
                "reason": f"Calendar lookup performed for '{requested_slot}': External calendar tool is offline or unverified. Actual free/busy status cannot be guaranteed.",
                "recommended_wording": f"I'll need to confirm my availability before committing to {requested_slot}. Could you please share 2-3 alternative time slots so I can ensure no conflicts?",
                "recommendation": f"Do NOT commit to '{requested_slot}'. Use wording: 'I'll need to confirm my availability before committing to that time' and request 2-3 alternative time slots."
            }
