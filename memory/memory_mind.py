"""
Memory Mind - Subconscious Memory Agent
Handles background memory consolidation and semantic operations
"""

import os
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from mind import execute_llm_call
from .index import MemoryIndex

class MemoryMind:
    """
    Subconscious memory agent that handles:
    - Semantic memory storage and retrieval
    - Background memory consolidation
    - Knowledge synthesis
    - Memory-driven context generation
    """
    
    def __init__(self, agent_name: str = "daemon"):
        self.agent_name = agent_name
        self.memory_index = MemoryIndex(f"memory/{agent_name}")
        
        # Memory agent configuration (can use different LLM)
        self.memory_llm_provider = os.getenv("MEMORY_LLM_PROVIDER", "openrouter")
        self.memory_llm_model = os.getenv("MEMORY_LLM_MODEL", "openai/gpt-4o")
        
        # Background processing
        self.consolidation_thread = None
        self.consolidation_interval = 300  # 5 minutes
        self.running = False
        
        # Consolidation state
        self.last_consolidation = datetime.now() - timedelta(hours=1)
        self.consolidation_threshold = 10  # Trigger after N new fragments
        
        print(f"🧠 Memory Mind initialized for '{agent_name}'")
        print(f"🔧 Memory LLM: {self.memory_llm_provider}/{self.memory_llm_model}")
    
    def start_background_processing(self):
        """Start background consolidation thread."""
        if self.consolidation_thread is None or not self.consolidation_thread.is_alive():
            self.running = True
            self.consolidation_thread = threading.Thread(
                target=self._background_consolidation_loop,
                daemon=True
            )
            self.consolidation_thread.start()
            print("🔄 Background memory consolidation started")
    
    def stop_background_processing(self):
        """Stop background consolidation."""
        self.running = False
        if self.consolidation_thread:
            self.consolidation_thread.join(timeout=5)
        print("⏹️ Background memory consolidation stopped")
    
    def store_memory(self, text: str, area: str = "fragments", metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Store a memory in the semantic index.
        
        Args:
            text: Memory content
            area: Memory area (fragments, solutions, contemplations, instruments)
            metadata: Additional metadata (tags, source, etc.)
            
        Returns:
            Memory ID if stored successfully
        """
        enhanced_metadata = metadata or {}
        enhanced_metadata.update({
            "stored_by": "memory_mind",
            "stored_at": datetime.now().isoformat()
        })
        
        memory_id = self.memory_index.add_text(text, area, enhanced_metadata)
        
        # Check if consolidation is needed
        if area == "fragments":
            self._check_consolidation_trigger()
        
        return memory_id
    
    def retrieve_memories(self, query: str, top_k: int = 10, area: Optional[str] = None,
                         min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Retrieve semantically similar memories.
        
        Args:
            query: Search query
            top_k: Number of results
            area: Filter by area
            min_score: Minimum similarity threshold
            
        Returns:
            List of relevant memories with scores
        """
        return self.memory_index.search(query, top_k, area, min_score)
    
    def get_context_for_conversation(self, user_input: str, conversation_history: List[str] = None,
                                   max_memories: int = 5) -> str:
        """
        Generate memory-driven context for conversation.
        
        Args:
            user_input: Current user input
            conversation_history: Recent conversation turns
            max_memories: Maximum memories to include
            
        Returns:
            Formatted context string
        """
        # Build search query from input and recent history
        search_query = user_input
        if conversation_history:
            recent_context = " ".join(conversation_history[-3:])  # Last 3 turns
            search_query = f"{user_input} {recent_context}"
        
        # Retrieve relevant memories
        memories = self.retrieve_memories(search_query, max_memories, min_score=0.4)
        
        if not memories:
            return ""
        
        # Format memories for context
        context_parts = ["## Relevant Memories:"]
        for memory in memories:
            area_emoji = {
                "solutions": "💡",
                "contemplations": "🤔", 
                "instruments": "🔧",
                "fragments": "📝"
            }.get(memory["area"], "📋")
            
            context_parts.append(
                f"{area_emoji} [{memory['area']}] {memory['text'][:200]}..."
                f" (relevance: {memory['score']:.2f})"
            )
        
        return "\n".join(context_parts)
    
    def consolidate_fragments(self, max_fragments: int = 20) -> Optional[str]:
        """
        Consolidate fragment memories into solutions using LLM.
        
        Args:
            max_fragments: Maximum fragments to consolidate at once
            
        Returns:
            ID of created solution summary, or None if no consolidation
        """
        print("🔄 Starting memory consolidation...")
        
        # Get recent fragments
        fragments = self.memory_index.get_by_area("fragments")
        if len(fragments) < 3:  # Need at least 3 fragments
            print("⚠️ Not enough fragments for consolidation")
            return None
        
        # Take most recent fragments
        fragments.sort(key=lambda x: x["created_at"], reverse=True)
        fragments_to_consolidate = fragments[:max_fragments]
        
        # Prepare consolidation prompt
        fragment_texts = [f"- {f['text']}" for f in fragments_to_consolidate]
        fragments_content = "\n".join(fragment_texts)
        
        system_prompt = """
You are a memory consolidation agent. Your task is to analyze fragments of experience and synthesize them into coherent insights, patterns, or solutions.

Create a concise summary that:
1. Identifies key themes and patterns
2. Extracts actionable insights
3. Connects related concepts
4. Preserves important details

Respond with a well-structured synthesis that could serve as a stable memory for future reference.
        """.strip()
        
        user_prompt = f"""
Consolidate these memory fragments into a coherent insight or solution:

{fragments_content}

Provide a clear, actionable synthesis that captures the essential patterns and insights.
        """
        
        try:
            # Use memory agent's LLM (can be different from main daemon)
            response = execute_llm_call(
                system_prompt,
                user_prompt,
                model=self.memory_llm_model
            )
            
            if "choices" in response and response["choices"]:
                synthesis = response["choices"][0]["message"]["content"]
                
                # Store as solution
                metadata = {
                    "type": "consolidation",
                    "source_fragments": [f["id"] for f in fragments_to_consolidate],
                    "fragment_count": len(fragments_to_consolidate),
                    "consolidated_by": "memory_mind"
                }
                
                solution_id = self.store_memory(synthesis, "solutions", metadata)
                
                print(f"✅ Consolidated {len(fragments_to_consolidate)} fragments into solution {solution_id}")
                return solution_id
            else:
                print("❌ LLM consolidation failed - no valid response")
                return None
                
        except Exception as e:
            print(f"❌ Error during consolidation: {e}")
            return None
    
    def _check_consolidation_trigger(self):
        """Check if consolidation should be triggered."""
        fragments = self.memory_index.get_by_area("fragments")
        
        # Trigger consolidation if enough new fragments
        if len(fragments) >= self.consolidation_threshold:
            time_since_last = datetime.now() - self.last_consolidation
            if time_since_last > timedelta(minutes=10):  # Minimum 10 minutes between consolidations
                print(f"🔔 Consolidation triggered: {len(fragments)} fragments")
                self.consolidate_fragments()
                self.last_consolidation = datetime.now()
    
    def _background_consolidation_loop(self):
        """Background thread for periodic consolidation."""
        while self.running:
            try:
                # Check for consolidation every interval
                time.sleep(self.consolidation_interval)
                
                if not self.running:
                    break
                
                # Periodic consolidation check
                fragments = self.memory_index.get_by_area("fragments")
                if len(fragments) >= self.consolidation_threshold:
                    time_since_last = datetime.now() - self.last_consolidation
                    if time_since_last > timedelta(minutes=30):  # Background: 30 min minimum
                        print("🌙 Background consolidation triggered")
                        self.consolidate_fragments()
                        self.last_consolidation = datetime.now()
                
            except Exception as e:
                print(f"❌ Error in background consolidation: {e}")
                time.sleep(60)  # Wait before retrying
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        stats = self.memory_index.get_stats()
        stats.update({
            "last_consolidation": self.last_consolidation.isoformat(),
            "consolidation_threshold": self.consolidation_threshold,
            "background_processing": self.running,
            "memory_llm": f"{self.memory_llm_provider}/{self.memory_llm_model}"
        })
        return stats
    
    def search_and_format(self, query: str, max_results: int = 5) -> str:
        """Search memories and return formatted results for display."""
        memories = self.retrieve_memories(query, max_results)
        
        if not memories:
            return f"No memories found for: {query}"
        
        result_lines = [f"🔍 Memory search results for '{query}':"]
        for i, memory in enumerate(memories, 1):
            area_emoji = {
                "solutions": "💡",
                "contemplations": "🤔",
                "instruments": "🔧", 
                "fragments": "📝"
            }.get(memory["area"], "📋")
            
            result_lines.append(
                f"{i}. {area_emoji} [{memory['area']}] {memory['text'][:150]}... "
                f"(score: {memory['score']:.2f})"
            )
        
        return "\n".join(result_lines)

# Global memory mind instance
_memory_mind = None

def get_memory_mind(agent_name: str = "daemon") -> MemoryMind:
    """Get singleton memory mind instance."""
    global _memory_mind
    if _memory_mind is None:
        _memory_mind = MemoryMind(agent_name)
    return _memory_mind
