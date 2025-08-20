import json
import os
import dotenv
from typing import Dict, Any
from datetime import datetime
from llm_factory import get_primary_client, get_reasoning_client, get_memory_client
import config

dotenv.load_dotenv()

# -----------------------------------------------------------------------------  
# Core API Interaction Functions
# -----------------------------------------------------------------------------
def execute_llm_call(system_prompt: str, user_prompt: str, model: str = None, client_type: str = "primary", **kwargs) -> Dict[str, Any]:
    """
    Executes a call to the configured LLM API using the model client adapter system.
    Returns a standardized response format compatible with existing daemon code.

    Args:
        system_prompt: The system prompt for the LLM
        user_prompt: The user's message/prompt
        model: Optional specific model override (if None, uses config default)
        client_type: Type of client to use ("primary", "reasoning", "memory")
        **kwargs: Additional parameters for the LLM call
    """
    print("\n" + "="*60)
    print(f"LLM INVOCATION at {datetime.now().isoformat()} | Client: {client_type}")

    try:
        # Select the appropriate client
        if client_type == "reasoning":
            adapter = get_reasoning_client()
            provider = config.REASONING_PROVIDER
            model_name = config.REASONING_MODEL
        elif client_type == "memory":
            adapter = get_memory_client()
            provider = config.MEMORY_LLM_PROVIDER
            model_name = config.MEMORY_LLM_MODEL
        else:  # primary (default)
            adapter = get_primary_client()
            provider = config.PRIMARY_PROVIDER
            model_name = config.PRIMARY_MODEL

        # Override model if specified
        if model is not None:
            model_name = model

        print(f"Provider: {provider} | Model: {model_name}")

        # Validate connection before making the call
        if not adapter.validate_connection():
            print(f"ERROR: Failed to validate connection to {provider}")
            return {"error": "Connection validation failed"}

        # Remove 'messages' from kwargs to avoid conflicts, since unified_call constructs its own messages
        filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'messages'}

        # Make the API call using the adapter's unified interface
        response_text, usage = adapter.unified_call(
            system_message=system_prompt,
            user_message=user_prompt,
            **filtered_kwargs
        )

        # Return in the format expected by existing daemon code
        return {
            "choices": [{
                "message": {
                    "content": response_text
                }
            }],
            "usage": usage
        }

    except Exception as e:
        print(f"ERROR: LLM call failed: {e}")
        return {"error": str(e)}

# -----------------------------------------------------------------------------  
# Convenience Functions for Different Client Types
# -----------------------------------------------------------------------------
def call_primary_llm(system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
    """Call the primary LLM for general operations."""
    return execute_llm_call(system_prompt, user_prompt, client_type="primary", **kwargs)

def call_reasoning_llm(system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
    """Call the reasoning LLM for complex operations."""
    return execute_llm_call(system_prompt, user_prompt, client_type="reasoning", **kwargs)

def call_memory_llm(system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
    """Call the memory LLM for background processing."""
    return execute_llm_call(system_prompt, user_prompt, client_type="memory", **kwargs)
