"""
OpenRouter Chat Adapter

Adapter for OpenRouter API, providing access to multiple LLM providers through a single interface.
Handles authentication, request formatting, and response parsing specific to OpenRouter.
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from .base_adapter import BaseChatAdapter, ChatMessage, ChatResponse


class OpenRouterChatAdapter(BaseChatAdapter):
    """
    Chat adapter for OpenRouter API.

    Provides a unified interface to multiple LLM providers through OpenRouter's routing system.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialize the OpenRouter adapter.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (e.g., 'openai/gpt-4o-mini', 'anthropic/claude-3-haiku')
            **kwargs: Additional configuration options
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/thamil33/deamon',  # Required by OpenRouter
            'X-Title': 'Daemon Framework',
        })

        # OpenRouter-specific configuration
        self.site_url = kwargs.get('site_url', 'https://github.com/thamil33/deamon')
        self.app_name = kwargs.get('app_name', 'Daemon Framework')

    def generate_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Generate a response using OpenRouter API.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenRouter-specific parameters

        Returns:
            ChatResponse object with generated content and metadata
        """
        try:
            # Prepare the request payload
            payload = self._prepare_request_payload(messages, temperature, max_tokens, **kwargs)

            # Make the API request
            response = self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
                timeout=kwargs.get('timeout', 30)
            )
            response.raise_for_status()

            # Parse the response
            return self._parse_response(response.json())

        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    def validate_connection(self) -> bool:
        """
        Validate connection to OpenRouter API.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Make a minimal request to test connectivity
            response = self.session.get(
                f"{self.BASE_URL}/models",
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

    def _prepare_request_payload(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: Optional[int],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare the request payload for OpenRouter API.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Dictionary containing the request payload
        """
        payload = {
            'model': self.model,
            'messages': [
                {'role': msg.role, 'content': msg.content}
                for msg in messages
            ],
            'temperature': max(0.0, min(2.0, temperature)),  # Clamp to valid range
        }

        # Add optional parameters if provided
        if max_tokens is not None:
            payload['max_tokens'] = max_tokens

        if 'top_p' in kwargs:
            payload['top_p'] = kwargs['top_p']

        if 'frequency_penalty' in kwargs:
            payload['frequency_penalty'] = kwargs['frequency_penalty']

        if 'presence_penalty' in kwargs:
            payload['presence_penalty'] = kwargs['presence_penalty']

        if 'stop' in kwargs:
            payload['stop'] = kwargs['stop']

        if 'seed' in kwargs:
            payload['seed'] = kwargs['seed']

        if 'transforms' in kwargs:
            payload['transforms'] = kwargs['transforms']

        return payload

    def _parse_response(self, response_data: Dict[str, Any]) -> ChatResponse:
        """
        Parse the OpenRouter API response into a ChatResponse object.

        Args:
            response_data: Raw response data from OpenRouter API

        Returns:
            ChatResponse object with extracted content and metadata
        """
        try:
            choice = response_data['choices'][0]
            message = choice['message']

            return ChatResponse(
                content=message.get('content', ''),
                usage=response_data.get('usage'),
                model=response_data.get('model'),
                finish_reason=choice.get('finish_reason')
            )
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse OpenRouter response: {str(e)}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter.

        Returns:
            List of model information dictionaries
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/models")
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch models: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model and configuration.

        Returns:
            Dictionary with model and configuration information
        """
        base_info = super().get_model_info()
        base_info.update({
            'provider_type': 'openrouter',
            'base_url': self.BASE_URL,
            'site_url': self.site_url,
            'app_name': self.app_name
        })
        return base_info
