"""
Unit Tests for AgentMail AI Planner Agent
Verifies deterministic decision safety overrides:
- Rule 1: Spam -> IGNORE
- Rule 2: Salary/Legal -> HUMAN_APPROVAL
- Rule 3: Unverified Interview/Meeting commitment -> HUMAN_APPROVAL
- Schema compliance
"""

import pytest
from backend.agents.planner import PlannerAgent


def test_planner_spam_override_to_ignore():
    planner = PlannerAgent()
    email_data = {
        "sender": "marketing@mega-deals.biz",
        "subject": "Win a free gift card today!",
        "body": "Click here to win a free shopping voucher."
    }
    classification = {
        "category": "Spam/Low Value",
        "intent": "Promotional spam",
        "priority": "Low",
        "sensitivity": "Low"
    }
    result = planner.plan(
        email_data=email_data,
        classification=classification,
        rag_context="No relevant context.",
        memory_context=""
    )
    assert result["decision"] == "IGNORE"
    assert "Spam" in result["reason"] or "promotional" in result["reason"].lower()


def test_planner_salary_override_to_human_approval():
    planner = PlannerAgent()
    email_data = {
        "sender": "hr@enterprise.com",
        "subject": "Salary discussion",
        "body": "Can you accept a CTC salary of 12 LPA per annum?"
    }
    classification = {
        "category": "Sensitive",
        "intent": "Salary negotiation",
        "priority": "High",
        "sensitivity": "High"
    }
    result = planner.plan(
        email_data=email_data,
        classification=classification,
        rag_context="Profile details.",
        memory_context=""
    )
    assert result["decision"] == "HUMAN_APPROVAL"
    assert "salary" in result["reason"].lower() or "sensitive" in result["reason"].lower()


def test_planner_interview_scheduling_without_calendar():
    planner = PlannerAgent()
    email_data = {
        "sender": "recruiter@talent.io",
        "subject": "Interview scheduling",
        "body": "Can we schedule an interview tomorrow at 3 PM?"
    }
    classification = {
        "category": "Interview",
        "intent": "Schedule technical interview",
        "priority": "High",
        "sensitivity": "Medium"
    }
    result = planner.plan(
        email_data=email_data,
        classification=classification,
        rag_context="Interview guidelines.",
        memory_context="",
        available_tools=["calendar_tool (status: offline)"]
    )
    # MUST NOT be AUTO_REPLY! Must be HUMAN_APPROVAL or CLARIFICATION_REQUIRED
    assert result["decision"] in ["HUMAN_APPROVAL", "CLARIFICATION_REQUIRED"]
    assert result["decision"] != "AUTO_REPLY"
    assert result["approval_required"] is True
    assert result["risk_level"] == "MEDIUM"
    assert result["approval_rule_applied"] == "RULE_CALENDAR_UNVERIFIED_GATE"


def test_planner_output_schema():
    planner = PlannerAgent()
    email_data = {
        "sender": "student@college.edu",
        "subject": "Project query",
        "body": "How did you implement the RAG retrieval pipeline?"
    }
    classification = {
        "category": "General",
        "intent": "Technical inquiry",
        "priority": "Medium",
        "sensitivity": "Low"
    }
    result = planner.plan(
        email_data=email_data,
        classification=classification,
        rag_context="RAG is implemented using nomic-embed-text.",
        memory_context=""
    )
    assert "decision" in result
    assert "priority" in result
    assert "risk_level" in result
    assert "approval_required" in result
    assert "approval_rule_applied" in result
    assert "reason" in result
    assert "confidence" in result
    assert "required_information" in result
    assert "recommended_action" in result
    assert result["decision"] in ["AUTO_REPLY", "HUMAN_APPROVAL", "CLARIFICATION_REQUIRED", "TOOL_REQUIRED", "IGNORE"]
