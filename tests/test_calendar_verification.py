"""
Unit Tests for Calendar Verification Accuracy (Issue #1 & Issue #4)
Verifies:
- Calendar result status is classified as AVAILABLE, CONFLICT, or UNVERIFIED.
- Recommended phrasing strictly avoids 'I have checked my schedule' when unverified.
- Automated commitments are blocked and routed to HUMAN_APPROVAL with RULE_CALENDAR_UNVERIFIED_GATE.
- Quality checker detects and flags misleading schedule claims.
"""

import pytest
from backend.tools.calendar_tool import CalendarAvailabilityTool
from backend.agents.planner import PlannerAgent
from backend.agents.writer import EmailWriterAgent
from backend.agents.quality_checker import QualityRiskCheckerAgent


def test_calendar_tool_unverified_offline():
    tool = CalendarAvailabilityTool(is_connected=False)
    res = tool.check_availability("Can we schedule an interview tomorrow at 3:00 PM IST?")

    assert res["lookup_performed"] is True
    assert "tomorrow at 3:00 pm" in res["requested_slot"].lower()
    assert res["availability_result"] == "UNVERIFIED"
    assert res["status"] == "UNVERIFIED_CALENDAR_OFFLINE"
    assert res["verified"] is False
    assert "confirm my availability before committing" in res["recommended_wording"]
    assert "checked my schedule" not in res["recommended_wording"]


def test_planner_blocks_unverified_calendar_commitments():
    planner = PlannerAgent()
    email_data = {
        "sender": "recruiter@innovators.tech",
        "subject": "Interview Invitation",
        "body": "Hi Pradeep, can we meet tomorrow at 3 PM for the technical round?"
    }
    classification = {
        "category": "Interview",
        "priority": "High",
        "sensitivity": "Medium"
    }
    plan = planner.plan(
        email_data=email_data,
        classification=classification,
        rag_context="Candidate guidelines.",
        memory_context=""
    )

    assert plan["decision"] == "HUMAN_APPROVAL"
    assert plan["approval_required"] is True
    assert plan["risk_level"] == "MEDIUM"
    assert plan["priority"] == "High"
    assert plan["approval_rule_applied"] == "RULE_CALENDAR_UNVERIFIED_GATE"
    assert "UNVERIFIED" in plan["reason"]


def test_writer_fallback_avoids_false_schedule_check():
    writer = EmailWriterAgent()
    email_data = {
        "sender": "recruiter@innovators.tech",
        "subject": "Technical Interview",
        "body": "Can you attend tomorrow at 3 PM?"
    }
    classification = {"category": "Interview", "priority": "High"}
    planner_decision = {
        "decision": "HUMAN_APPROVAL",
        "priority": "High",
        "risk_level": "MEDIUM",
        "approval_required": True,
        "calendar_audit": {
            "lookup_performed": True,
            "availability_result": "UNVERIFIED",
            "status": "UNVERIFIED_CALENDAR_OFFLINE",
            "requested_slot": "tomorrow at 3 PM",
            "recommended_wording": "I will need to confirm my availability before committing to tomorrow at 3 PM."
        }
    }

    # Simulate fallback generation (without LLM dependency)
    draft = writer.draft_response(
        email_data=email_data,
        classification=classification,
        planner_decision=planner_decision,
        rag_context="Candidate: Pradeep Kumar A.",
        memory_context=""
    )

    body_lower = draft["body"].lower()
    # Must NOT claim that schedule was checked
    assert "i have checked my schedule" not in body_lower
    assert "i checked my schedule" not in body_lower
    # Must state need to confirm availability or request alternatives
    assert "confirm" in body_lower or "alternative" in body_lower


def test_quality_checker_flags_misleading_schedule_claims():
    checker = QualityRiskCheckerAgent()
    misleading_draft = {
        "subject": "Re: Interview Invitation",
        "body": "Dear Recruiter, I have checked my schedule and can confirm tomorrow at 3 PM works."
    }
    original_email = {"body": "Can you meet tomorrow at 3 PM?"}

    audit = checker.audit(
        draft_response=misleading_draft,
        original_email=original_email,
        rag_context="External calendar is offline.",
        memory_context="",
        planner_decision="HUMAN_APPROVAL"
    )

    assert audit["approved"] is False
    assert audit["approval_required"] is True
    assert any("checked" in issue.lower() or "commitment" in issue.lower() for issue in audit["issues"])
