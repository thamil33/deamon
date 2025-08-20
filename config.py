"""
Centralized configuration management for the daemon.
Loads settings from the .env file and provides them as easily accessible constants.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Provider Configuration ---
# Primary provider for general daemon operations
PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "openrouter")

# Optional: Dedicated provider for complex reasoning (defaults to PRIMARY_PROVIDER if not set)
REASONING_PROVIDER = os.getenv("REASONING_PROVIDER") or PRIMARY_PROVIDER

# API keys and URLs
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", "")
LMPROXY_BASE_URL = os.getenv("LMPROXY_BASE_URL", "http://localhost:8080")
LMPROXY_API_KEY = os.getenv("LMPROXY_API_KEY", "")

# --- Model Configuration ---
# Primary model for general daemon operations
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "openai/gpt-4o-mini")

# Optional: Dedicated model for complex reasoning (defaults to PRIMARY_MODEL if not set)
REASONING_MODEL = os.getenv("REASONING_MODEL") or PRIMARY_MODEL



# --- Memory Mind (Subconscious) Configuration ---
# The model used for background memory consolidation.
MEMORY_LLM_PROVIDER = os.getenv("MEMORY_LLM_PROVIDER", "openrouter")
MEMORY_LLM_MODEL = os.getenv("MEMORY_LLM_MODEL", "anthropic/claude-3-haiku")

# --- Embedding Model Configuration ---
# The model used for creating semantic embeddings for memory.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# --- Validate that essential keys are set ---
if PRIMARY_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
    raise ValueError("PRIMARY_PROVIDER is set to 'openrouter' but OPENROUTER_API_KEY is not set in .env")
if PRIMARY_PROVIDER == "lmstudio" and not LM_STUDIO_API_KEY:
    print("WARNING: LM_STUDIO_API_KEY is not set. Using default 'lm-studio'.")
if PRIMARY_PROVIDER == "lmproxy" and not LMPROXY_BASE_URL:
    print("WARNING: LMPROXY_BASE_URL is not set. Using default 'http://localhost:8080'.")

if MEMORY_LLM_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
    raise ValueError("MEMORY_LLM_PROVIDER is set to 'openrouter' but OPENROUTER_API_KEY is not set in .env")

print("✅ Configuration loaded successfully.")
print(f"Primary Provider: {PRIMARY_PROVIDER}")
print(f"Primary Model: {PRIMARY_MODEL}")
print(f"Reasoning Provider: {REASONING_PROVIDER}")
print(f"Reasoning Model: {REASONING_MODEL}")
print(f"Memory Provider: {MEMORY_LLM_PROVIDER}")
print(f"Memory Model: {MEMORY_LLM_MODEL}")
