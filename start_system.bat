@echo off
TITLE AgentMail AI - Intelligent Email Management System
COLOR 0B

echo ===============================================================================
echo     ___                    __  __            _ _         _    ___ 
echo    /   ^| ____ ____  ____  / /_/  ^|___ _____ (_) /        / \  ^|_ _^|
echo   / /^| ^|/ __ `/ _ \/ __ \/ __/ /^|_/ __ `/ / / / _____   / _ \  ^| ^| 
echo  / ___ / /_/ /  __/ / / / /_/ /  / /_/ / / / / /_____/ / ___ \ ^| ^| 
echo /_/  ^|_\__, /\___/_/ /_/\__/_/  /\__,_/_/_/_/         /_/   \_\___^|
echo       /____/                                                       
echo    AgentMail AI: An Agentic AI-Based Intelligent Email Management System
echo    Final-Year B.Tech Capstone Project in Artificial Intelligence ^& Data Science
echo ===============================================================================

echo [1/4] Checking Python environment...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in system PATH!
    pause
    exit /b 1
)

echo [2/4] Verifying Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Ollama does not appear to be running at http://localhost:11434!
    echo Please start Ollama by opening the Ollama application or running 'ollama serve'.
    echo Continuing startup in fallback mode...
) ELSE (
    echo [OK] Ollama is active and reachable.
)

echo [3/4] Initializing Database and Knowledge Base...
python -c "from backend.database.db import init_db; from backend.rag.vector_store import LocalVectorStore; init_db(); vs = LocalVectorStore(); vs.index_knowledge_base(); print('Database and RAG Vector Store initialized.')"

echo [4/4] Starting AgentMail AI FastAPI Server and Web Dashboard on http://localhost:8000...
start "" http://localhost:8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
