"""
Memory Index Manager
FAISS-based vector search with metadata management
"""

import faiss
import json
import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
import hashlib

from .embedder import get_embedder

class MemoryRecord:
    """Individual memory record with vector and metadata."""
    
    def __init__(self, text: str, area: str = "main", metadata: Optional[Dict] = None):
        self.id = str(uuid.uuid4())
        self.text = text
        self.area = area
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        self.vector_id = None  # Set when added to FAISS index
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "area": self.area,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "hash": self.hash,
            "vector_id": self.vector_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRecord':
        """Create from dictionary."""
        record = cls(data["text"], data["area"], data.get("metadata", {}))
        record.id = data["id"]
        record.created_at = data["created_at"]
        record.hash = data["hash"]
        record.vector_id = data.get("vector_id")
        return record

class MemoryIndex:
    """FAISS-based memory index with metadata management."""
    
    def __init__(self, root_path: str = "memory/daemon"):
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.meta_path = self.root_path / "index.pkl"
        self.faiss_path = self.root_path / "index.faiss"
        self.embedding_meta_path = self.root_path / "embedding.json"
        
        # Initialize components
        self.embedder = get_embedder()
        self.records: List[MemoryRecord] = []
        self.id_to_record: Dict[str, MemoryRecord] = {}
        self.hash_to_record: Dict[str, MemoryRecord] = {}
        
        # FAISS index
        self.index = None
        self.next_vector_id = 0
        
        # Load existing data
        self._load()
        self._save_embedder_meta()
        
        print(f"📚 Memory index initialized: {len(self.records)} records")
    
    def _load(self):
        """Load existing records and FAISS index."""
        # Load metadata
        if self.meta_path.exists():
            try:
                with open(self.meta_path, 'rb') as f:
                    data = pickle.load(f)
                    self.records = [MemoryRecord.from_dict(r) for r in data["records"]]
                    self.next_vector_id = data.get("next_vector_id", len(self.records))
                    
                    # Build lookup dictionaries
                    for record in self.records:
                        self.id_to_record[record.id] = record
                        self.hash_to_record[record.hash] = record
                        
                print(f"✅ Loaded {len(self.records)} memory records")
            except Exception as e:
                print(f"⚠️ Error loading metadata: {e}")
                self.records = []
        
        # Load FAISS index
        if self.faiss_path.exists() and len(self.records) > 0:
            try:
                self.index = faiss.read_index(str(self.faiss_path))
                print(f"✅ Loaded FAISS index: {self.index.ntotal} vectors")
            except Exception as e:
                print(f"⚠️ Error loading FAISS index: {e}")
                self._rebuild_index()
        else:
            self._initialize_index()
    
    def _initialize_index(self):
        """Initialize empty FAISS index."""
        self.index = faiss.IndexFlatIP(self.embedder.dim)  # Inner product (cosine with normalized vectors)
        print(f"🔧 Initialized new FAISS index ({self.embedder.dim}D)")
    
    def _rebuild_index(self):
        """Rebuild FAISS index from existing records."""
        print("🔄 Rebuilding FAISS index...")
        self._initialize_index()
        
        if self.records:
            texts = [r.text for r in self.records]
            vectors = self.embedder.embed(texts)
            self.index.add(vectors)
            
            # Update vector IDs
            for i, record in enumerate(self.records):
                record.vector_id = i
            
            self.next_vector_id = len(self.records)
            print(f"✅ Rebuilt index with {len(self.records)} vectors")
    
    def _save(self):
        """Save records and FAISS index to disk."""
        # Save metadata
        data = {
            "records": [r.to_dict() for r in self.records],
            "next_vector_id": self.next_vector_id
        }
        
        with open(self.meta_path, 'wb') as f:
            pickle.dump(data, f)
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, str(self.faiss_path))
    
    def _save_embedder_meta(self):
        """Save embedder metadata."""
        with open(self.embedding_meta_path, 'w') as f:
            json.dump(self.embedder.info, f, indent=2)
    
    def add_text(self, text: str, area: str = "main", metadata: Optional[Dict] = None, 
                 force: bool = False) -> Optional[str]:
        """
        Add text to the memory index.
        
        Args:
            text: Text content to add
            area: Memory area (main, fragments, solutions, instruments)
            metadata: Additional metadata
            force: Force add even if duplicate hash exists
            
        Returns:
            Record ID if added, None if duplicate
        """
        # Check for duplicates unless forced
        if not force:
            text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            if text_hash in self.hash_to_record:
                print(f"⚠️ Duplicate text detected, skipping...")
                return None
        
        # Create record
        record = MemoryRecord(text, area, metadata)
        
        # Generate embedding
        vector = self.embedder.embed_single(record.text)
        
        # Add to FAISS index
        if self.index is None:
            self._initialize_index()
        
        vector_reshaped = vector.reshape(1, -1)
        self.index.add(vector_reshaped)
        record.vector_id = self.next_vector_id
        self.next_vector_id += 1
        
        # Store record
        self.records.append(record)
        self.id_to_record[record.id] = record
        self.hash_to_record[record.hash] = record
        
        # Save to disk
        self._save()
        
        print(f"📝 Added memory: {record.area}/{record.id[:8]} ({len(text)} chars)")
        return record.id
    
    def add_texts(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Batch add multiple texts.
        
        Args:
            items: List of dicts with keys: text, area, metadata
            
        Returns:
            List of record IDs
        """
        if not items:
            return []
        
        records = []
        texts = []
        
        # Create records and collect texts
        for item in items:
            record = MemoryRecord(
                item["text"], 
                item.get("area", "main"), 
                item.get("metadata", {})
            )
            
            # Check for duplicates
            if record.hash not in self.hash_to_record:
                records.append(record)
                texts.append(record.text)
        
        if not records:
            print("⚠️ No new records to add (all duplicates)")
            return []
        
        # Generate embeddings in batch
        vectors = self.embedder.embed(texts)
        
        # Add to FAISS index
        if self.index is None:
            self._initialize_index()
        
        self.index.add(vectors)
        
        # Update records and store
        added_ids = []
        for i, record in enumerate(records):
            record.vector_id = self.next_vector_id + i
            self.records.append(record)
            self.id_to_record[record.id] = record
            self.hash_to_record[record.hash] = record
            added_ids.append(record.id)
        
        self.next_vector_id += len(records)
        self._save()
        
        print(f"📚 Batch added {len(records)} memories")
        return added_ids
    
    def search(self, query: str, top_k: int = 20, area_filter: Optional[str] = None,
               min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Semantic search for memories.
        
        Args:
            query: Search query
            top_k: Number of results to return
            area_filter: Filter by memory area
            min_score: Minimum similarity score
            
        Returns:
            List of matching records with scores
        """
        if not self.records or self.index is None:
            return []
        
        # Generate query embedding
        query_vector = self.embedder.embed_single(query)
        query_reshaped = query_vector.reshape(1, -1)
        
        # Search FAISS index
        scores, indices = self.index.search(query_reshaped, min(top_k * 2, len(self.records)))
        
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < 0 or idx >= len(self.records):
                continue
                
            if score < min_score:
                continue
            
            record = self.records[idx]
            
            # Apply area filter
            if area_filter and record.area != area_filter:
                continue
            
            result = {
                "id": record.id,
                "text": record.text,
                "area": record.area,
                "metadata": record.metadata,
                "created_at": record.created_at,
                "score": float(score),
                "rank": rank
            }
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        print(f"🔍 Search '{query[:50]}...' found {len(results)} results")
        return results
    
    def get_by_area(self, area: str) -> List[Dict[str, Any]]:
        """Get all records from a specific area."""
        results = []
        for record in self.records:
            if record.area == area:
                results.append({
                    "id": record.id,
                    "text": record.text,
                    "area": record.area,
                    "metadata": record.metadata,
                    "created_at": record.created_at
                })
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        area_counts = {}
        for record in self.records:
            area_counts[record.area] = area_counts.get(record.area, 0) + 1
        
        return {
            "total_records": len(self.records),
            "total_vectors": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedder.dim,
            "areas": area_counts,
            "embedder_info": self.embedder.info
        }
    
    def reindex(self) -> Dict[str, Any]:
        """Rebuild the entire index."""
        print("🔄 Reindexing memory...")
        old_count = len(self.records)
        self._rebuild_index()
        self._save()
        
        stats = self.get_stats()
        print(f"✅ Reindexing complete: {old_count} -> {stats['total_records']} records")
        return stats
