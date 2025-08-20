"""
Base Chat Adapter

Abstract base class defining the common interface for all LLM provider adapters.
This ensures consistent behavior across different providers while allowing
for provider-specific optimizations and features.
"""

import abc
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """Represents a single message in a chat conversation."""
    role: str  # 'system', 'user', or 'assistant'
    content: str


@dataclass
class ChatResponse:
    """Represents a response from the LLM provider."""
    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class BaseChatAdapter(abc.ABC):
    """
    Abstract base class for LLM chat adapters.

    All provider-specific adapters should inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, model: str, **kwargs):
        """
        Initialize the adapter with model and provider-specific configuration.

        Args:
            model: The model identifier to use
            **kwargs: Additional provider-specific configuration
        """
        self.model = model
        self.config = kwargs

    @abc.abstractmethod
    def generate_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse object containing the generated content and metadata
        """
        pass

    @abc.abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that the adapter can connect to the provider.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    def prepare_messages(
        self,
        messages: Union[List[Dict[str, str]], List[ChatMessage]]
    ) -> List[ChatMessage]:
        """
        Convert various message formats to ChatMessage objects.

        Args:
            messages: Messages in various formats (dict or ChatMessage)

        Returns:
            List of ChatMessage objects
        """
        if not messages:
            return []

        if isinstance(messages[0], ChatMessage):
            return messages

        # Convert from dict format
        return [
            ChatMessage(role=msg.get('role', 'user'), content=msg.get('content', ''))
            for msg in messages
        ]

    def unified_call(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Unified interface for simple system + user message calls.

        Args:
            system_message: The system prompt
            user_message: The user message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Tuple of (response_content, usage_metadata)
        """
        messages = [
            ChatMessage(role='system', content=system_message),
            ChatMessage(role='user', content=user_message)
        ]

        response = self.generate_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        return response.content, response.usage

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model and configuration.

        Returns:
            Dictionary with model information
        """
        return {
            'model': self.model,
            'provider': self.__class__.__name__,
            'config': self.config
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model='{self.model}')"
