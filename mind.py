import json
import os
import requests 
import dotenv 
from typing import Dict, Any
from datetime import datetime

dotenv.load_dotenv() 

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YOUR_SITE_URL = os.getenv("YOUR_SITE_URL")
YOUR_SITE_NAME = os.getenv("YOUR_SITE_NAME")

# Add a configuration variable to select the LLM API provider
LLM_API_PROVIDER = os.getenv("LLM_API_PROVIDER", "openrouter")  # Default to 'openrouter'

# -----------------------------------------------------------------------------
# Core API Interaction Function
# -----------------------------------------------------------------------------
def execute_llm_call(system_prompt: str, user_prompt: str, model: str = "openai/gpt-4o", **kwargs) -> Dict[str, Any]:
    """
    Executes a call to the selected LLM API and returns the JSON response.
    """
    if LLM_API_PROVIDER == "lmproxy":
        response_text, _ = lmproxy_adapter.unified_call(
            system_message=system_prompt,
            user_message=user_prompt,
            **kwargs
        )
        return {"choices": [{"message": {"content": response_text}}]}

    # Default to OpenRouter API
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY environment variable not set.")
        # Return a simulated response to prevent crashing
        return {"error": "API Key not configured."}

    print("\n" + "="*60)
    print(f"LLM INVOCATION at {datetime.now().isoformat()} | Model: {model}")
    
    # Base payload
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    # Merge any additional keyword arguments (like response_format) into the payload
    payload.update(kwargs)
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            data=json.dumps(payload)
        )
        response.raise_for_status() 
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API CALL FAILED: {e}")
        return {"error": str(e)}

class LMProxyChatAdapter:
    """Adapter for VS Code LM Proxy (or any OpenAI-compatible proxy endpoint).

    Implements the unified_call interface used by Agent. Streams chunks and
    invokes callbacks similar to LiteLLMChatWrapper.unified_call.
    """

    def __init__(self, provider: str, model: str, api_base: str = "http://localhost:4000", **kwargs: Any):
        self.provider = provider
        self.model = model
        self.base_url = api_base.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        self.kwargs = kwargs or {}

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        if not messages:
            return []
        return messages

    def unified_call(
        self,
        system_message: str = "",
        user_message: str = "",
        messages: list[dict] | None = None,
        **kwargs: Any,
    ) -> tuple[str, str]:
        # Build messages array
        msgs: list[dict] = []
        if messages:
            msgs = self._convert_messages(messages)
        if system_message:
            msgs.insert(0, {"role": "system", "content": system_message})
        if user_message:
            msgs.append({"role": "user", "content": user_message})

        # Prepare request
        url = f"{self.base_url}/openai/v1/chat/completions"
        payload = {"model": self.model, "messages": msgs, "stream": True}
        merged_kwargs = {**self.kwargs, **kwargs}
        for k, v in merged_kwargs.items():
            if k in ("api_base",):
                continue
            payload.setdefault(k, v)

        response_text = ""
        reasoning_text = ""

        # Perform streaming HTTP request
        try:
            resp = requests.post(url, headers=self.headers, json=payload, stream=True)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"[LMProxy error] {e}", reasoning_text

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            data_str = line
            if data_str.startswith("data: "):
                data_str = data_str[len("data: ") :]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            response_delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            response_text += response_delta

        return response_text, reasoning_text

if LLM_API_PROVIDER == "lmproxy":
    lmproxy_adapter = LMProxyChatAdapter(provider="lmproxy", model="openai/gpt-4o")
