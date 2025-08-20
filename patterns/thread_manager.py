import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class ThreadManager:
    """Manages prompt threads/patterns for the daemon."""
    
    def __init__(self, patterns_dir: str = "patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.threads: Dict[str, Dict[str, Any]] = {}
        self._load_threads()
    
    def _load_threads(self):
        """Load all thread files from the patterns directory."""
        if not self.patterns_dir.exists():
            self.patterns_dir.mkdir(exist_ok=True)
            return
        
        for file_path in self.patterns_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    thread_data = json.load(f)
                    thread_name = file_path.stem
                    self.threads[thread_name] = thread_data
                    print(f"Loaded thread: {thread_name}")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading thread {file_path}: {e}")
    
    def get_thread(self, thread_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific thread by name."""
        return self.threads.get(thread_name)
    
    def list_threads(self) -> List[str]:
        """List all available thread names."""
        return list(self.threads.keys())
    
    def get_system_prompt(self, thread_name: str) -> str:
        """Get the system prompt for a specific thread."""
        thread = self.get_thread(thread_name)
        if thread:
            # Handle both simple instruction lists and complex system prompts
            if "system_prompt" in thread:
                return thread["system_prompt"]
            elif "instructions" in thread:
                return "\n".join(thread["instructions"])
        return ""
    
    def load_thread_from_file(self, file_path: str):
        """Load a single thread from a specific file path."""
        path = Path(file_path)
        if not path.exists():
            print(f"Error: Thread file not found at {file_path}")
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                thread_data = json.load(f)
                thread_name = path.stem
                self.threads[thread_name] = thread_data
                print(f"Loaded single thread: {thread_name}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading thread {file_path}: {e}")
    
    def get_thread_context(self, thread_name: str) -> Dict[str, Any]:
        """Get the full context for a thread including all metadata."""
        return self.get_thread(thread_name) or {}
    
    def apply_thread_spell(self, thread_name: str, spell_name: str) -> Optional[Dict[str, Any]]:
        """Apply a specific spell from a thread."""
        thread = self.get_thread(thread_name)
        if thread and "spells" in thread:
            return thread["spells"].get(spell_name)
        return None
