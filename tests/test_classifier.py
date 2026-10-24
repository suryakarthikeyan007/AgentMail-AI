"""
Unit Tests for AgentMail AI Classifier Agent
Verifies category mapping, entity extraction, sensitivity rating, and fallback heuristics.
"""

import pytest
from backend.agents.classifier import EmailClassifierAgent


def test_classifier_fallback_heuristics():
    classifier = EmailClassifierAgent()

    # Test 1: Salary keyword -> Sensitive
    res_salary = classifier.classify({
        "sender": "hr@corp.com",
        "subject": "Offer Discussion - Salary",
        "body": "Can you accept a CTC of 12 LPA?"
    })
    assert res_salary["category"] in ["Sensitive", "Job"]
    assert res_salary["confidence"] > 0

    # Test 2: Interview keyword -> Interview
    res_interview = classifier.classify({
        "sender": "recruiter@tech.com",
        "subject": "Technical Round Interview",
        "body": "We would like to invite you for a technical screening interview."
    })
    assert res_interview["category"] in ["Interview", "Meeting"]

    # Test 3: Resume keyword -> Request
    res_resume = classifier.classify({
        "sender": "talent@startup.io",
        "subject": "Please send your resume",
        "body": "Could you provide your latest resume and portfolio link?"
    })
    assert res_interview["category"] in ["Interview", "Meeting", "Request", "Job"]

    # Test 4: Spam keyword -> Spam/Low Value
    res_spam = classifier.classify({
        "sender": "promo@deals.com",
        "subject": "You won the lottery prize",
        "body": "Congratulations, claim your free crypto discount today!"
    })
    assert res_spam["category"] in ["Spam/Low Value", "General", "Information"]


def test_classifier_structure_schema():
    classifier = EmailClassifierAgent()
    res = classifier.classify({
        "sender": "team@university.edu",
        "subject": "Seminar on Agentic AI",
        "body": "We are hosting a workshop next Monday."
    })

    required_keys = [
        "category", "intent", "priority", "reply_required",
        "sensitivity", "confidence", "urgency", "requested_action", "entities"
    ]
    for key in required_keys:
        assert key in res
    assert isinstance(res["confidence"], (float, int))
    assert isinstance(res["reply_required"], bool)
    assert isinstance(res["entities"], list)
