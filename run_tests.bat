@echo off
TITLE AgentMail AI - Test Suite Runner
COLOR 0A

echo ===============================================================================
echo AgentMail AI: Automated Academic Verification ^& Test Suite
echo ===============================================================================

echo [1/3] Running Unit Tests (Preprocessor, Safety Gate, Quality Critic, RAG)...
pytest tests/test_preprocessor.py tests/test_safety_checker.py tests/test_rag_memory.py -v

echo.
echo [2/3] Running 10 Formal Final-Year Project Test Cases...
python tests/test_10_cases.py

echo.
echo [3/3] Running Academic Benchmark Metrics Evaluation...
python evaluate.py

echo.
echo ===============================================================================
echo Academic verification completed.
echo ===============================================================================
pause
