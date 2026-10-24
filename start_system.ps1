# AgentMail AI - PowerShell Startup Script
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "   AgentMail AI: An Agentic AI-Based Intelligent Email Management System" -ForegroundColor Cyan
Write-Host "   Final-Year B.Tech Capstone Project in Artificial Intelligence & Data Science" -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Cyan

Write-Host "[1/4] Checking Python environment..." -ForegroundColor Green
$pythonVersion = python --version 2>&1
Write-Host "      Detected: $pythonVersion" -ForegroundColor Gray

Write-Host "[2/4] Verifying Ollama service..." -ForegroundColor Green
try {
    $ollamaCheck = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "      Ollama active at http://localhost:11434 with models:" -ForegroundColor Gray
    $ollamaCheck.models | ForEach-Object { Write-Host "      - $($_.name)" -ForegroundColor Gray }
} catch {
    Write-Host "      [WARNING] Ollama is not responding at http://localhost:11434!" -ForegroundColor Magenta
    Write-Host "      Ensure Ollama is running or start it using 'ollama serve'." -ForegroundColor Magenta
}

Write-Host "[3/4] Initializing Database & Local Vector Store..." -ForegroundColor Green
python -c "from backend.database.db import init_db; from backend.rag.vector_store import LocalVectorStore; init_db(); vs = LocalVectorStore(); vs.index_knowledge_base(); print('      Database & Knowledge Base verified.')"

Write-Host "[4/4] Starting FastAPI Server & Web Dashboard..." -ForegroundColor Green
Start-Process "http://localhost:8000"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
