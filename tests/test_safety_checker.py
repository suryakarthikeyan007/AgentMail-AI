"""
Unit Tests for AgentMail AI Safety Gate and Quality Risk Checker
"""

import pytest
from backend.safety.safety_gate import SafetyGate
from backend.agents.quality_checker import QualityRiskCheckerAgent


def test_safety_gate_blocks_high_risk_auto_reply():
    gate = SafetyGate(test_mode=True)
    planner_decision = {
        "decision": "AUTO_REPLY",
        "reason": "Attempted auto reply"
    }
    # Quality audit detected high risk
    quality_audit = {
        "approved": False,
        "risk_level": "HIGH",
        "issues": ["Ungrounded interview date commitment"]
    }

    action, reason = gate.evaluate_routing(planner_decision, quality_audit)
    assert action == "HUMAN_APPROVAL"
    assert "Safety override" in reason


def test_safety_gate_passes_low_risk_auto_reply():
    gate = SafetyGate(test_mode=True)
    planner_decision = {
        "decision": "AUTO_REPLY",
        "reason": "Safe factual acknowledgement"
    }
    quality_audit = {
        "approved": True,
        "risk_level": "LOW",
        "issues": []
    }

    action, reason = gate.evaluate_routing(planner_decision, quality_audit)
    assert action == "AUTO_REPLY"


def test_quality_checker_flags_hallucinated_interview_time():
    checker = QualityRiskCheckerAgent()
    draft = {
        "subject": "Re: Interview",
        "body": "Hi John, sure, let us meet tomorrow at 3 PM for the technical round."
    }
    original = {"body": "Can we meet tomorrow?"}

    # Deterministic check
    audit = checker.audit(
        draft_response=draft,
        original_email=original,
        rag_context="No calendar access.",
        memory_context="",
        planner_decision="AUTO_REPLY"
    )

    assert audit["risk_level"] == "HIGH"
    assert audit["approved"] is False
    assert any("calendar commitment" in issue for issue in audit["issues"])
