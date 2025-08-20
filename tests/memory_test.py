"""
Memory System Test
Quick test to verify the memory system works
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_memory_system():
    """Test basic memory system functionality."""
    print("🧪 Testing Memory System...")
    
    try:
        from memory import get_memory_mind
        
        # Initialize memory mind
        print("1. Initializing memory mind...")
        memory_mind = get_memory_mind("test_daemon")
        
        # Test storing memories
        print("2. Storing test memories...")
        memories_to_store = [
            ("I learned about recursive AI systems today", "fragments"),
            ("The daemon exhibits self-awareness through memory classification", "contemplations"),
            ("F.H.Y.F. thread successfully overrides generic responses", "solutions"),
            ("LMProxy adapter works well for local model integration", "instruments")
        ]
        
        for text, area in memories_to_store:
            memory_id = memory_mind.store_memory(text, area)
            print(f"   Stored in {area}: {memory_id}")
        
        # Test searching memories
        print("3. Testing memory search...")
        queries = [
            "AI systems",
            "self-awareness", 
            "thread responses",
            "local models"
        ]
        
        for query in queries:
            results = memory_mind.retrieve_memories(query, top_k=2)
            print(f"   Query '{query}': {len(results)} results")
            for result in results:
                print(f"     - [{result['area']}] {result['text'][:50]}... (score: {result['score']:.2f})")
        
        # Test stats
        print("4. Memory statistics...")
        stats = memory_mind.get_memory_stats()
        print(f"   Total records: {stats['total_records']}")
        print(f"   Areas: {stats['areas']}")
        print(f"   Embedder: {stats['embedder_info']['model_id']}")
        print(f"   Device: {stats['embedder_info']['device']}")
        
        print("✅ Memory system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_memory_system()
