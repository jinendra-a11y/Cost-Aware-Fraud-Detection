import json
from langchain_groq import ChatGroq
from .base import BaseProvider, ProviderResponse
import os
from pathlib import Path
from typing import Any

# Define paths relative to this file
CURRENT_DIR = Path(__file__).resolve().parent
NORMALIZE_PROMPT_FILE = CURRENT_DIR / "NORMALIZE_PROMPT_FILE"
FRAUD_DETECTION_PROMPT = CURRENT_DIR / "FRAUD_DETECTION_PROMPT"


class GroqProvider(BaseProvider):
    def __init__(self, model_name="llama3-8b-8192"):
        # We don't hardcode the model in __init__ anymore, but accepting it for compatibility
        pass

    def execute(self, *args, **kwargs) -> ProviderResponse:
        """
        Satisfies the BaseProvider abstract method.
        Not used directly by services.py which calls specific methods.
        """
        raise NotImplementedError("Use normalize_bills or evaluate_fraud instead.")

    def _execute(self, model_name: str, system_prompt: str, user_payload: Any) -> ProviderResponse:
        """Internal helper to handle the actual API call."""
        llm = ChatGroq(model=model_name, temperature=0.1)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)}
        ]
        
        response = llm.invoke(messages)
        usage = response.response_metadata.get('token_usage', {})
        
        return ProviderResponse(
            content=response.content,
            input_units=usage.get('prompt_tokens', 0),
            output_units=usage.get('completion_tokens', 0),
            model_name=model_name
        )

    async def normalize_bills(self, raw_texts: list) -> ProviderResponse:
        # Use a faster, cheaper model for normalization
        model = "llama-3.1-8b-instant"
        with open(NORMALIZE_PROMPT_FILE, "r") as f:
            system_prompt = f.read()
        return self._execute(model, system_prompt, {"raw_bill_inputs": raw_texts})

    async def evaluate_fraud(self, job_details: dict, bills: list, mode: str) -> ProviderResponse:
        # Use a larger, smarter model for complex fraud analysis
        model = "llama-3.3-70b-versatile" 
        with open(FRAUD_DETECTION_PROMPT, "r") as f:
            system_prompt = f.read()        
        return self._execute(model, system_prompt, {"job": job_details, "bills": bills})