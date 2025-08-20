# Model Client Adapters

This package provides a unified interface for interacting with different Large Language Model (LLM) providers. It abstracts away the differences between various APIs and provides a consistent interface for the daemon framework.

## Architecture

The adapter system follows a clean architecture pattern:

- **`BaseChatAdapter`**: Abstract base class defining the common interface
- **Provider-specific adapters**: Concrete implementations for each LLM provider
- **Factory pattern**: Centralized creation and configuration of adapters

## Available Adapters

### OpenRouterChatAdapter

Provides access to multiple LLM providers through OpenRouter's unified API.

**Features:**
- Access to 20+ LLM providers (OpenAI, Anthropic, Google, etc.)
- Automatic provider routing and fallbacks
- Built-in rate limiting and cost optimization
- Model availability monitoring

**Configuration:**
```python
adapter = OpenRouterChatAdapter(
    api_key="your-openrouter-api-key",
    model="openai/gpt-4o-mini",
    site_url="https://your-site.com",  # Optional
    app_name="Your App"               # Optional
)
```

### LMStudioChatAdapter

Provides access to locally hosted models through OpenAI-compatible APIs (LM Studio, text-generation-webui, etc.).

**Features:**
- Support for local model inference
- OpenAI-compatible API interface
- Configurable timeout for local inference
- Optional API key authentication

**Configuration:**
```python
adapter = LMStudioChatAdapter(
    base_url="http://localhost:1234/v1",
    model="local-model-name",
    api_key="optional-api-key"
)
```

## Usage

### Basic Usage

```python
from model_client_adapters import get_model_client

# Get a configured adapter
adapter = get_model_client(provider="openrouter", model="openai/gpt-4o-mini")

# Generate a response
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
]

response = adapter.generate_response(
    messages=messages,
    temperature=0.7,
    max_tokens=100
)

print(response.content)
```

### Unified Interface

```python
# Simple system + user message pattern
response_text, usage = adapter.unified_call(
    system_message="You are a helpful assistant.",
    user_message="Explain quantum computing in simple terms.",
    temperature=0.7
)
```

### Direct Adapter Usage

```python
from model_client_adapters import OpenRouterChatAdapter

adapter = OpenRouterChatAdapter(
    api_key="your-api-key",
    model="anthropic/claude-3-haiku"
)

# Validate connection
if adapter.validate_connection():
    print("✅ Connection successful")

# Get available models
models = adapter.get_available_models()
print(f"Available models: {len(models)}")

# Get adapter info
info = adapter.get_model_info()
print(f"Provider: {info['provider_type']}")
```

## Configuration

The adapters are configured through environment variables in your `.env` file:

```env
# Provider selection
LLM_API_PROVIDER=openrouter  # or 'lmproxy'

# OpenRouter configuration
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_XTRA_URL=https://your-site.com
OPENROUTER_XTRA_TITLE=Your App Name

# LMProxy/LM Studio configuration
LM_STUDIO_URL=http://127.0.0.1:1234/v1
LM_STUDIO_API_KEY=lm-studio  # Optional
```

## Error Handling

All adapters include comprehensive error handling:

- **Connection errors**: Network issues, invalid endpoints
- **Authentication errors**: Invalid API keys
- **Rate limiting**: Automatic retry with exponential backoff
- **Model errors**: Invalid models, context length exceeded

```python
try:
    response = adapter.generate_response(messages)
    print(response.content)
except Exception as e:
    print(f"Error: {e}")
```

## Testing

Run the test suite to verify adapter functionality:

```bash
python model_client_adapters/test_adapters.py
```

The tests validate:
- Adapter initialization
- Message conversion
- Interface compliance
- Error handling

## Adding New Providers

To add support for a new LLM provider:

1. Create a new adapter class inheriting from `BaseChatAdapter`
2. Implement the required abstract methods:
   - `generate_response()`
   - `validate_connection()`
3. Update the factory function in `llm_factory.py`
4. Add imports to `__init__.py`
5. Write tests for the new adapter

Example:

```python
from .base_adapter import BaseChatAdapter, ChatMessage, ChatResponse

class NewProviderAdapter(BaseChatAdapter):
    def generate_response(self, messages, **kwargs):
        # Implement provider-specific logic
        pass

    def validate_connection(self):
        # Implement connection validation
        pass
```

## Best Practices

1. **Use the factory**: Always use `get_model_client()` instead of direct instantiation
2. **Handle errors**: Wrap API calls in try-catch blocks
3. **Validate connections**: Check `validate_connection()` before heavy usage
4. **Monitor usage**: Use the `usage` metadata for cost tracking
5. **Configuration**: Keep sensitive data in environment variables

## Dependencies

- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- Standard library: `abc`, `typing`, `dataclasses`

## License

This package is part of the daemon framework and follows the same license terms.
