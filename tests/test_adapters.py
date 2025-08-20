"""
Test script for the new model client adapter system.

This script tests the simplified PRIMARY/REASONING configuration system
and ensures all components work together correctly.
"""

import sys
import os

# Ensure repository root (one level up from /tests) is on sys.path so the package can be imported
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from model_client_adapters import BaseChatAdapter, OpenRouterChatAdapter, LMStudioChatAdapter, LMProxyChatAdapter
from model_client_adapters.base_adapter import ChatResponse, ChatMessage
from llm_factory import get_primary_client, get_reasoning_client, get_memory_client, get_model_client
import config

def test_base_adapter():
    """Test the base adapter interface."""
    print("Testing BaseChatAdapter...")

    # Create a mock adapter
    class MockAdapter(BaseChatAdapter):
        def generate_response(self, messages, **kwargs):
            return self._create_mock_response("Mock response")

        def validate_connection(self):
            return True

        def _create_mock_response(self, content):
            from model_client_adapters.base_adapter import ChatResponse
            return ChatResponse(
                content=content,
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                model="mock-model",
                finish_reason="stop"
            )

    adapter = MockAdapter("mock-model")

    # Test unified_call
    response, usage = adapter.unified_call(
        system_message="You are a helpful assistant.",
        user_message="Hello!"
    )

    assert response == "Mock response"
    assert usage is not None
    print("✅ Base adapter test passed")


def test_openrouter_adapter():
    """Test OpenRouter adapter initialization."""
    print("Testing OpenRouterChatAdapter...")

    # Test with dummy API key (won't make real calls)
    adapter = OpenRouterChatAdapter(
        api_key="dummy-key",
        model="openai/gpt-4o-mini"
    )

    assert adapter.model == "openai/gpt-4o-mini"
    assert adapter.api_key == "dummy-key"

    # Test get_model_info
    info = adapter.get_model_info()
    assert info['provider_type'] == 'openrouter'
    assert info['model'] == "openai/gpt-4o-mini"

    print("✅ OpenRouter adapter test passed")


def test_lmstudio_adapter():
    """Test LMStudio adapter initialization."""
    print("Testing LMStudioChatAdapter...")

    # Test with dummy configuration
    adapter = LMStudioChatAdapter(
        base_url="http://localhost:1234/v1",
        model="openai/gpt-4o",
        api_key="dummy-key"
    )

    assert adapter.model == "openai/gpt-4o"
    assert adapter.base_url == "http://localhost:1234/v1"
    assert adapter.api_key == "dummy-key"

    # Test get_model_info
    info = adapter.get_model_info()
    assert info['provider_type'] == 'lmstudio'
    assert info['base_url'] == "http://localhost:1234/v1"

    print("✅ LMStudio adapter test passed")


def test_lmproxy_adapter():
    """Test LMProxy adapter initialization."""
    print("Testing LMProxyChatAdapter...")

    # Test with dummy configuration
    adapter = LMProxyChatAdapter(
        base_url="http://localhost:8080",
        model="gpt-4.1",
        api_key="dummy-key"
    )

    assert adapter.model == "gpt-4.1"
    assert adapter.base_url == "http://localhost:8080"
    assert adapter.api_key == "dummy-key"

    # Test get_model_info
    info = adapter.get_model_info()
    assert info['provider_type'] == 'lmproxy'
    assert info['base_url'] == "http://localhost:8080"

    print("✅ LMProxy adapter test passed")


def test_chat_message_conversion():
    """Test message conversion functionality."""
    print("Testing message conversion...")

    adapter = LMStudioChatAdapter(
        base_url="http://localhost:1234/v1",
        model="test-model"
    )

    # Test dict to ChatMessage conversion
    dict_messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"}
    ]

    chat_messages = adapter.prepare_messages(dict_messages)
    assert len(chat_messages) == 2
    assert isinstance(chat_messages[0], ChatMessage)
    assert chat_messages[0].role == "system"
    assert chat_messages[0].content == "You are helpful."

    print("✅ Message conversion test passed")


def test_configuration_system():
    """Test the new simplified configuration system."""
    print("Testing configuration system...")

    # Test config variables are loaded
    assert hasattr(config, 'PRIMARY_PROVIDER')
    assert hasattr(config, 'PRIMARY_MODEL')
    assert hasattr(config, 'REASONING_PROVIDER')
    assert hasattr(config, 'REASONING_MODEL')

    # Test fallback logic
    assert config.REASONING_PROVIDER is not None  # Should fallback to PRIMARY_PROVIDER
    assert config.REASONING_MODEL is not None     # Should fallback to PRIMARY_MODEL

    # Test backward compatibility variables
    assert hasattr(config, 'LLM_API_PROVIDER')
    assert hasattr(config, 'EVOLUTION_MODEL')
    assert hasattr(config, 'RITUAL_MODEL')

    print("✅ Configuration system test passed")


def test_factory_functions():
    """Test the new factory functions for different client types."""
    print("Testing factory functions...")

    # Test primary client factory
    primary_client = get_primary_client()
    assert primary_client is not None
    assert hasattr(primary_client, 'validate_connection')
    assert hasattr(primary_client, 'unified_call')

    # Test reasoning client factory
    reasoning_client = get_reasoning_client()
    assert reasoning_client is not None
    assert hasattr(reasoning_client, 'validate_connection')
    assert hasattr(reasoning_client, 'unified_call')

    # Test memory client factory
    memory_client = get_memory_client()
    assert memory_client is not None
    assert hasattr(memory_client, 'validate_connection')
    assert hasattr(memory_client, 'unified_call')

    # Test direct model client factory
    direct_client = get_model_client(config.PRIMARY_PROVIDER, config.PRIMARY_MODEL)
    assert direct_client is not None

    print("✅ Factory functions test passed")


def test_client_types():
    """Test that different client types are correctly configured."""
    print("Testing client types...")

    # Test primary client configuration
    primary = get_primary_client()
    info = primary.get_model_info()
    assert 'provider_type' in info
    assert 'model' in info

    # Test reasoning client configuration
    reasoning = get_reasoning_client()
    info = reasoning.get_model_info()
    assert 'provider_type' in info
    assert 'model' in info

    # Test memory client configuration
    memory = get_memory_client()
    info = memory.get_model_info()
    assert 'provider_type' in info
    assert 'model' in info

    print("✅ Client types test passed")


def test_extensibility():
    """Test that the system is extensible for future provider/model roles."""
    print("Testing extensibility...")

    # Test that we can add new client types by extending the factory
    # This is more of a structural test to ensure the system is designed for extension

    # Verify that the factory can handle different providers
    openrouter_client = get_model_client('openrouter', 'test-model')
    lmproxy_client = get_model_client('lmproxy', 'test-model')
    lmstudio_client = get_model_client('lmstudio', 'test-model')

    assert isinstance(openrouter_client, OpenRouterChatAdapter)
    assert isinstance(lmproxy_client, LMProxyChatAdapter)
    assert isinstance(lmstudio_client, LMStudioChatAdapter)

    # Verify that config has all the necessary pieces for extension
    assert hasattr(config, 'PRIMARY_PROVIDER')
    assert hasattr(config, 'REASONING_PROVIDER')
    assert hasattr(config, 'MEMORY_LLM_PROVIDER')

    print("✅ Extensibility test passed")


def main():
    """Run all tests."""
    print("Running model client adapter tests...\n")

    try:
        test_base_adapter()
        test_openrouter_adapter()
        test_lmstudio_adapter()
        test_lmproxy_adapter()
        test_chat_message_conversion()
        test_configuration_system()
        test_factory_functions()
        test_client_types()
        test_extensibility()

        print("\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
