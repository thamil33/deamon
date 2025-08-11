import json
import os
import threading
import time
import uuid
import shutil
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, Any, List
import dotenv 

# load environment variables from .env file

# -----------------------------------------------------------------------------
# Core API Interaction Function
# -----------------------------------------------------------------------------
def execute_llm_call(system_prompt: str, user_prompt: str, model: str = "openai/gpt-4o") -> Dict[str, Any]:
    """
    Executes a call to the OpenRouter API and returns the JSON response.
    This is the single point of contact with the external LLM.
    """
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY environment variable not set.")
        # Return a simulated response to prevent crashing
        return {"error": "API Key not configured."}

    print("\n" + "="*60)
    print(f"LLM INVOCATION at {datetime.now().isoformat()} | Model: {model}")
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_SITE_NAME,
            },
            data=json.dumps({ 
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            })
        )
        response.raise_for_status() # Raises an exception for bad status codes
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API CALL FAILED: {e}")
        return {"error": str(e)}
