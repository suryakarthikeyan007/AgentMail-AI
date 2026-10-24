"""
Unit Tests for AgentMail AI RAG Vector Store & Conversation Memory
Verifies chunking, vector indexing, similarity search, and thread memory persistence.
"""

import pytest
from backend.database.db import init_db
from backend.rag.vector_store import LocalVectorStore
from backend.rag.retriever import RAGRetriever
from backend.memory.conversation_memory import ConversationMemoryManager


def test_rag_chunking_and_retrieval():
    init_db()
    vs = LocalVectorStore()
    indexed_count = vs.index_knowledge_base()
    assert indexed_count > 0

    retriever = RAGRetriever(vs)
    res = retriever.retrieve_context("What is your CGPA and university education?", top_k=2)

    assert "formatted_text" in res
    assert len(res["chunks"]) > 0
    assert any("education" in c["category"].lower() or "profile" in c["category"].lower() for c in res["chunks"])


def test_conversation_memory_multi_turn():
    import uuid
    init_db()
    memory = ConversationMemoryManager()
    thread_id = f"test_memory_thread_{uuid.uuid4().hex[:8]}"

    # Turn 1: Initial Email
    turn1 = memory.update_thread_memory(
        thread_id=thread_id,
        sender="recruiter@alpha.com",
        subject="Interview Inquiry",
        incoming_message="Are you available for an interview next week?",
        category="Interview",
        planner_decision="HUMAN_APPROVAL",
        response_summary="Awaiting supervisor availability review.",
        extracted_facts=["Interview", "Alpha Corp"]
    )
    assert turn1["turn_count"] == 1
    assert turn1["is_existing_conversation"] is False

    # Turn 2: Follow-up in same thread
    turn2 = memory.update_thread_memory(
        thread_id=thread_id,
        sender="recruiter@alpha.com",
        subject="Re: Interview Inquiry",
        incoming_message="Can you also confirm if you know Python and Agentic AI?",
        category="Job",
        planner_decision="AUTO_REPLY",
        response_summary="Confirmed Python expertise from RAG.",
        extracted_facts=["Python", "Agentic AI"]
    )
    assert turn2["turn_count"] == 2
    assert turn2["is_existing_conversation"] is True
    assert "Interview" in turn2["key_facts"]
    assert "Python" in turn2["key_facts"]

    # Verify formatted prompt context
    prompt_str = memory.format_memory_for_prompt(thread_id)
    assert "Turn 1" in prompt_str
    assert "Turn 2" in prompt_str
    assert thread_id in prompt_str
