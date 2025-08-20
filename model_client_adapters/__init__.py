"""
Model Client Adapters Package

This package provides adapter classes for different LLM providers,
ensuring a consistent interface across all supported services.
"""

from .base_adapter import BaseChatAdapter
from .openrouter_adapter import OpenRouterChatAdapter
from .lm_studio import LMStudioChatAdapter
from .lm_proxy import LMProxyChatAdapter

__all__ = [
    'BaseChatAdapter',
    'OpenRouterChatAdapter',
    'LMStudioChatAdapter',
    'LMProxyChatAdapter'
]
