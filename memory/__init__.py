"""
Memory System Package
Provides semantic memory with FAISS indexing and background consolidation
"""

from .embedder import LocalEmbedder, get_embedder
from .index import MemoryIndex, MemoryRecord
from .memory_mind import MemoryMind, get_memory_mind

__all__ = [
    'LocalEmbedder',
    'get_embedder', 
    'MemoryIndex',
    'MemoryRecord',
    'MemoryMind',
    'get_memory_mind'
]
