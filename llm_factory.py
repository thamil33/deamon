"""
LLM Client Factory
This module provides a centralized factory for creating and configuring LLM clients.
It abstracts away the logic of which adapter to use based on the provider
and ensures that clients are created with the correct configuration.
"""
import config
from model_client_adapters import LMStudioChatAdapter, OpenRouterChatAdapter, LMProxyChatAdapter

def get_model_client(provider: str, model: str):
    """
    Factory function to get a configured model client instance.

    Args:
        provider (str): The LLM provider (e.g., 'openrouter', 'lmproxy').
        model (str): The specific model identifier.

    Returns:
        An instance of a chat adapter (e.g., OpenRouterChatAdapter, LMStudioChatAdapter)
        or raises ValueError if the provider is unknown.
    """
    if provider == 'openrouter':
        return OpenRouterChatAdapter(
            api_key=config.OPENROUTER_API_KEY,
            model=model
        )
    elif provider == 'lmproxy':
        return LMProxyChatAdapter(
            base_url=config.LMPROXY_BASE_URL,
            model=model,
            api_key=config.LMPROXY_API_KEY
        )
    elif provider == 'lmstudio':
        return LMStudioChatAdapter(
            base_url=config.LM_STUDIO_URL,
            model=model,
            api_key=config.LM_STUDIO_API_KEY
        )
    else:
        raise ValueError(f"Unknown LLM provider specified: {provider}")

def get_primary_client():
    """Get a model client for primary/general operations."""
    return get_model_client(config.PRIMARY_PROVIDER, config.PRIMARY_MODEL)

def get_reasoning_client():
    """Get a model client for complex reasoning operations."""
    return get_model_client(config.REASONING_PROVIDER, config.REASONING_MODEL)

def get_memory_client():
    """Get a model client for memory processing operations."""
    return get_model_client(config.MEMORY_LLM_PROVIDER, config.MEMORY_LLM_MODEL)
