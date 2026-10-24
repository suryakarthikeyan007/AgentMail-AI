"""
Unit Tests for AgentMail AI Email Preprocessor
"""

import pytest
from backend.agents.preprocessor import EmailPreprocessor


def test_clean_html_and_signatures():
    preprocessor = EmailPreprocessor()
    raw_html_email = {
        "sender": "John Recruiter <john@hr.com>",
        "subject": "Greetings",
        "body": """
        <div>
            <p>Hi Pradeep,</p>
            <p>We received your application. Could you confirm your interest?</p>
            <br>
            --
            <br>
            John Recruiter<br>
            Talent Acquisition Specialist<br>
            Best regards,<br>
            Sent from my iPhone
        </div>
        """
    }

    result = preprocessor.process(raw_html_email)
    body = result["body"]

    assert "confirm your interest" in body
    assert "<div>" not in body
    assert "<p>" not in body
    assert "Sent from my iPhone" not in body
    assert result["sender"] == "John Recruiter <john@hr.com>"


def test_quote_history_removal():
    preprocessor = EmailPreprocessor()
    raw_email = {
        "sender": "sarah@tech.org",
        "subject": "Re: Discussion",
        "body": """
        Yes, let us connect next week.

        On Mon, Oct 5, 2026 at 10:00 AM Sarah <sarah@tech.org> wrote:
        > Are you free to discuss?
        > Let me know your thoughts.
        """
    }

    result = preprocessor.process(raw_email)
    assert "Yes, let us connect next week." in result["body"]
    assert "On Mon, Oct 5" not in result["body"]
    assert "> Are you free" not in result["body"]
