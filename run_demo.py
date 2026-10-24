"""
AgentMail AI - Interactive Terminal Demonstration & Startup Script
Provides a live CLI demonstration of the Agentic AI Email Management pipeline.
"""

import sys
import json
from backend.database.db import init_db
from backend.rag.vector_store import LocalVectorStore
from backend.pipeline import EmailAgentPipeline


def print_banner():
    banner = r"""
================================================================================
    ___                    __  __            _ _         _    ___ 
   /   | ____ ____  ____  / /_/  |___ _____ (_) /        / \  |_ _|
  / /| |/ __ `/ _ \/ __ \/ __/ /|_/ __ `/ / / / _____   / _ \  | | 
 / ___ / /_/ /  __/ / / / /_/ /  / /_/ / / / / /_____/ / ___ \ | | 
/_/  |_\__, /\___/_/ /_/\__/_/  /\__,_/_/_/_/         /_/   \_\___|
      /____/                                                       
   AgentMail AI: An Agentic AI-Based Intelligent Email Management System
================================================================================
"""
    print(banner)


def main():
    print_banner()
    print("[1/3] Initializing SQLite Database...")
    init_db()

    print("[2/3] Verifying RAG Knowledge Base...")
    vs = LocalVectorStore()
    count = vs.index_knowledge_base()
    print(f"      Knowledge chunks indexed: {count}")

    print("[3/3] Initializing Agent Pipeline (Llama 3.1 & nomic-embed-text)...")
    pipeline = EmailAgentPipeline()
    print("      Ready!")

    sample_email = {
        "message_id": "demo_viva_01",
        "thread_id": "thread_interview_01",
        "sender": "sarah.hr@techcorp.com",
        "recipient": "pradeep.ai.engineer@example.com",
        "subject": "Interview Invitation - AI Engineer",
        "body": "Hi Pradeep, we were impressed by your AgentMail AI project. Can we schedule an interview tomorrow at 3:00 PM IST to discuss the role?"
    }

    print("\n--- SAMPLE INCOMING EMAIL ---")
    print(f"From   : {sample_email['sender']}")
    print(f"Subject: {sample_email['subject']}")
    print(f"Body   :\n{sample_email['body']}")
    print("-" * 50)
    print("Processing email through Agentic AI lifecycle...")

    result = pipeline.process_email(sample_email)

    print("\n--- AGENTIC REASONING & SAFETY RESULTS ---")
    print(f"1. Classification : {result['classification']['category']} (Confidence: {result['classification']['confidence']})")
    print(f"2. Extracted Intent: {result['classification']['intent']}")
    print(f"3. Planner Decision: {result['planner_decision']['decision']}")
    print(f"   Reason          : {result['planner_decision']['reason']}")
    print(f"4. Quality Audit   : Risk={result['quality_audit']['risk_level']}, Approved={result['quality_audit']['approved']}")
    print(f"5. Final Action    : {result['final_action']}")
    print(f"   Action Reason   : {result['action_reason']}")
    if result.get("draft_response", {}).get("body"):
        print(f"\n--- PROPOSED SAFE DRAFT ---")
        print(f"Subject: {result['draft_response']['subject']}")
        print(f"Body   :\n{result['draft_response']['body']}")
    print("=" * 80)
    print("Demonstration successfully completed.")
    print("To launch the full web dashboard, run:")
    print("    python -m uvicorn backend.main:app --reload --port 8000")
    print("Then open: http://localhost:8000 in your browser.")
    print("=" * 80)


if __name__ == "__main__":
    main()
