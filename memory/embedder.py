"""
Local Embedder for Daemon Memory System
Uses HuggingFace sentence-transformers with CUDA optimization
"""

from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import os
from typing import List
import hashlib
import json
from pathlib import Path

class LocalEmbedder:
    """Local embedding system using sentence-transformers with CUDA optimization."""
    
    def __init__(self, model_id: str = None, cache_dir: str = None):
        # Use environment variable or default model
        self.model_id = model_id or os.getenv("EMBEDDER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        # Use environment variable for cache directory
        self.cache_dir = cache_dir or os.getenv("HUGGINGFACE_HUB_CACHE", "memory/.cache")
        
        # Ensure cache directory exists
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Auto-detect device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"🧠 Initializing embedder: {self.model_id}")
        print(f"🔧 Device: {self.device}")
        print(f"📁 Cache: {self.cache_dir}")
        
        # Initialize model
        self.model = SentenceTransformer(
            self.model_id, 
            device=self.device,
            cache_folder=self.cache_dir
        )
        
        # Embedding cache for deduplication
        self.cache_file = Path(self.cache_dir) / "embedding_cache.json"
        self.embedding_cache = self._load_cache()
        
    def _load_cache(self) -> dict:
        """Load embedding cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def _save_cache(self):
        """Save embedding cache to disk."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.embedding_cache, f)
    
    def _get_text_hash(self, text: str) -> str:
        """Generate SHA256 hash of text for caching."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def embed(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """
        Embed list of texts with optional caching.
        
        Args:
            texts: List of strings to embed
            use_cache: Whether to use/update embedding cache
            
        Returns:
            Normalized embeddings as numpy array
        """
        if not texts:
            return np.array([])
        
        embeddings = []
        texts_to_embed = []
        cache_keys = []
        
        # Check cache for existing embeddings
        if use_cache:
            for text in texts:
                text_hash = self._get_text_hash(text)
                if text_hash in self.embedding_cache:
                    # Use cached embedding
                    cached_emb = np.array(self.embedding_cache[text_hash])
                    embeddings.append(cached_emb)
                    cache_keys.append(None)  # Mark as cached
                else:
                    # Need to embed
                    texts_to_embed.append(text)
                    cache_keys.append(text_hash)
                    embeddings.append(None)  # Placeholder
        else:
            texts_to_embed = texts
            cache_keys = [None] * len(texts)
            embeddings = [None] * len(texts)
        
        # Embed new texts in batches
        if texts_to_embed:
            print(f"🔮 Embedding {len(texts_to_embed)} new texts...")
            new_embeddings = self.model.encode(
                texts_to_embed,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=len(texts_to_embed) > 10
            )
            
            # Insert new embeddings and update cache
            new_idx = 0
            cache_updated = False
            
            for i, cache_key in enumerate(cache_keys):
                if cache_key is not None:  # New embedding needed
                    emb = new_embeddings[new_idx]
                    embeddings[i] = emb
                    
                    if use_cache:
                        # Cache the embedding
                        self.embedding_cache[cache_key] = emb.tolist()
                        cache_updated = True
                    
                    new_idx += 1
            
            # Save cache if updated
            if cache_updated:
                self._save_cache()
        
        # Convert to numpy array
        result = np.array(embeddings, dtype=np.float32)
        
        print(f"✅ Generated {len(result)} embeddings ({result.shape[1]}D)")
        return result
    
    def embed_single(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Embed a single text string."""
        result = self.embed([text], use_cache=use_cache)
        return result[0] if len(result) > 0 else np.array([])
    
    @property
    def dim(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()
    
    @property
    def info(self) -> dict:
        """Get embedder information."""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "dimension": self.dim,
            "cache_size": len(self.embedding_cache),
            "normalize": True
        }
    
    def clear_cache(self):
        """Clear embedding cache."""
        self.embedding_cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        print("🗑️ Embedding cache cleared")

# Singleton instance for global use
_embedder_instance = None

def get_embedder() -> LocalEmbedder:
    """Get singleton embedder instance."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = LocalEmbedder()
    return _embedder_instance
