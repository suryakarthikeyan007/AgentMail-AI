"""
AgentMail AI - Configuration Module
Loads settings from environment variables or .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Ollama LLM & Embedding Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:latest")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180.0"))

# Application Settings
APP_ENV = os.getenv("APP_ENV", "development")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
TEST_MODE = os.getenv("TEST_MODE", "true").lower() in ("true", "1", "yes")

# Database & Storage
DATABASE_PATH = BASE_DIR / "agentmail.db"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"

# Gmail Credentials (for live Gmail API when TEST_MODE=false)
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:5678/rest/oauth2-credential/callback")
GMAIL_USER_EMAIL = os.getenv("GMAIL_USER_EMAIL", "demo.student@gmail.com")
