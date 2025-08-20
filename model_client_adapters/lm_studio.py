"""
LM-Studio / OpenAI compatible Chat Adapter

Adapter for LM Studio API, providing access to locally hosted or proxied LLM models.
Handles OpenAI-compatible API calls for local model inference.
"""

import requests
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from .base_adapter import BaseChatAdapter, ChatMessage, ChatResponse


class LMStudioChatAdapter(BaseChatAdapter):
    """
    Chat adapter for LM-Studio, or another local OpenAI Compatible API.

    Provides access to locally hosted models through an OpenAI-compatible API interface.
    Typically used with LM Studio or other local model servers.
    """

    def __init__(self, base_url: str, model: str, api_key: str = "", **kwargs):
        """
        Initialize the LMProxy adapter.

        Args:
            base_url: Base URL of the LMProxy/LM Studio server (e.g., 'http://localhost:1234')
            model: Model identifier
            api_key: API key (optional for local servers)
            **kwargs: Additional configuration options
        """
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        # Set up headers
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        self.session.headers.update(headers)

        # Default timeout for local requests
        self.default_timeout = kwargs.get('timeout', 60)  # Longer timeout for local inference

    def generate_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Generate a response using LMProxy/LM Studio API.

        Args:
            messages: List of chat messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional LMProxy-specific parameters

        Returns:
            ChatResponse object with generated content and metadata
        """
        try:
            # Prepare the request payload
            payload = self._prepare_request_payload(messages, temperature, max_tokens, **kwargs)

            # Make the API request
            endpoint = urljoin(self.base_url + '/', 'v1/chat/completions')
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=kwargs.get('timeout', self.default_timeout)
            )
            response.raise_for_status()

            # Parse the response
            return self._parse_response(response.json())

        except requests.exceptions.RequestException as e:
            raise Exception(f"LMProxy API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    def validate_connection(self) -> bool:
        """
        Validate connection to LMProxy/LM Studio server.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to access the models endpoint to test connectivity
            endpoint = urljoin(self.base_url + '/', 'v1/models')
            response = self.session.get(endpoint, timeout=10)
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
        Prepare the request payload for LMProxy API.

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
            'stream': False  # We don't support streaming in this implementation
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

        if 'logit_bias' in kwargs:
            payload['logit_bias'] = kwargs['logit_bias']

        # LMProxy-specific parameters
        if 'top_k' in kwargs:
            payload['top_k'] = kwargs['top_k']

        if 'repeat_penalty' in kwargs:
            payload['repeat_penalty'] = kwargs['repeat_penalty']

        if 'presence_penalty' in kwargs:
            payload['presence_penalty'] = kwargs['presence_penalty']

        return payload

    def _parse_response(self, response_data: Dict[str, Any]) -> ChatResponse:
        """
        Parse the LMProxy API response into a ChatResponse object.

        Args:
            response_data: Raw response data from LMProxy API

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
            raise Exception(f"Failed to parse LMProxy response: {str(e)}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from LMProxy server.

        Returns:
            List of model information dictionaries
        """
        try:
            endpoint = urljoin(self.base_url + '/', 'v1/models')
            response = self.session.get(endpoint)
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
            'provider_type': 'lmstudio',
            'base_url': self.base_url,
            'has_api_key': bool(self.api_key)
        })
        return base_info

    def get_server_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the LMProxy server.

        Returns:
            Dictionary with server information, or None if unavailable
        """
        try:
            # Some LMProxy servers might have an info endpoint
            endpoint = urljoin(self.base_url + '/', 'v1/info')
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
