# This file can be used for dynamic thread generation or custom thread logic
# For now, threads are managed via JSON files in the patterns directory

from thread_manager import ThreadManager

def create_custom_thread(name: str, system_prompt: str, spells: dict = None):
    """Helper function to create custom threads programmatically."""
    thread_data = {
        "thread_name": name,
        "system_prompt": system_prompt,
        "spells": spells or {},
        "created_dynamically": True
    }
    return thread_data