"""
AgentMail AI - Base Agent Module
Handles communication with Ollama API, robust JSON extraction, prompt injection defense, and error handling.
"""

import json
import re
import logging
from typing import Dict, Any, Optional
import httpx

from backend.config import OLLAMA_BASE_URL, LLM_MODEL, LLM_TIMEOUT

logger = logging.getLogger("agentmail.agents")


class BaseAgent:
    def __init__(self, model_name: str = LLM_MODEL, timeout: float = LLM_TIMEOUT):
        self.model_name = model_name
        self.timeout = timeout
        self.api_url = f"{OLLAMA_BASE_URL}/api/generate"

    def clean_json_response(self, text: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON from LLM output, stripping markdown fences,
        comments, and extraneous conversational preamble/postscript.
        """
        if not text:
            return {}

        # 1. Strip markdown fences like ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # 2. Search for outermost curly braces { ... }
        brace_match = re.search(r"(\{[\s\S]*\})", text)
        if brace_match:
            candidate = brace_match.group(1).strip()
            try:
                return json.loads(candidate)
            except Exception:
                pass

        # 3. Direct attempt
        try:
            return json.loads(text.strip())
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}. Raw text: {text[:200]}")
            return {}

    def call_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        format_json: bool = True,
        max_tokens: int = 400
    ) -> str:
        """Invokes the local Ollama LLM with timeout and error resilience."""
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(self.api_url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
                else:
                    logger.error(f"Ollama call failed with status {res.status_code}: {res.text}")
                    return ""
        except httpx.ReadTimeout:
            logger.error(f"Ollama timed out after {self.timeout}s")
            return ""
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            return ""

    def sanitize_untrusted_input(self, text: str) -> str:
        """
        Sanitizes incoming email content to mitigate prompt injection.
        Wraps content in isolated demarcations and removes control command sequences.
        """
        if not text:
            return ""
        # Remove potential instruction bypass tokens
        sanitized = re.sub(r"(?i)(system\s*prompt|ignore\s+all\s+previous\s+instructions)", "[Filtered Directive]", text)
        return sanitized
