"""
Individual Component Tests
Tests each component in isolation to identify bottlenecks
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_mind_module():
    """Test the mind module directly."""
    print("🧠 Testing mind.py module...")
    
    try:
        from mind import execute_llm_call, LLM_API_PROVIDER, LMStudioChatAdapter
        print(f"✓ Mind module imported successfully")
        print(f"✓ LLM_API_PROVIDER: {LLM_API_PROVIDER}")
        
        # Test if LMStudioChatAdapter is being used
        if LLM_API_PROVIDER == "lmproxy":
            print("✓ LMProxy mode detected")
            # Test adapter creation
            adapter = LMStudioChatAdapter(provider="lmproxy", model="test")
            print("✓ LMStudioChatAdapter created successfully")
        else:
            print("✓ OpenRouter mode detected")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in mind module: {e}")
        return False

def test_thread_manager_isolation():
    """Test ThreadManager in complete isolation."""
    print("\n🧵 Testing ThreadManager in isolation...")
    
    try:
        from patterns.thread_manager import ThreadManager
        
        # Test basic instantiation
        tm = ThreadManager()
        print("✓ ThreadManager instantiated")
        
        # Test thread listing
        threads = tm.list_threads()
        print(f"✓ Threads found: {threads}")
        
        # Test specific thread loading
        for thread_name in threads:
            thread_data = tm.get_thread(thread_name)
            if thread_data:
                print(f"✓ Thread '{thread_name}' loaded successfully")
                # Test system prompt extraction
                system_prompt = tm.get_system_prompt(thread_name)
                print(f"✓ System prompt extracted: {len(system_prompt)} chars")
            else:
                print(f"❌ Thread '{thread_name}' failed to load")
                
        return True
        
    except Exception as e:
        print(f"❌ Error in ThreadManager: {e}")
        return False

def test_prompt_content():
    """Test actual content of prompts."""
    print("\n📝 Testing prompt content...")
    
    try:
        from patterns.thread_manager import ThreadManager
        
        tm = ThreadManager()
        fhyf_prompt = tm.get_system_prompt("fhyf_core")
        
        print("F.H.Y.F. System Prompt Content:")
        print("-" * 50)
        print(repr(fhyf_prompt))  # Use repr to see exact content including newlines
        print("-" * 50)
        
        # Check for key rejection phrases
        rejection_checks = [
            "How can I assist you today",
            "I'm here to help",
            "What can I do for you"
        ]
        
        print("\nRejection phrase checks:")
        for phrase in rejection_checks:
            found = phrase in fhyf_prompt
            print(f"  '{phrase}': {'FOUND' if found else 'NOT FOUND'}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing prompt content: {e}")
        return False

def test_conversation_flow():
    """Test the conversation flow step by step."""
    print("\n💬 Testing conversation flow...")
    
    try:
        # Import daemon components
        from deamon import handle_conversation, build_dynamic_system_prompt
        
        # Test system prompt building
        print("1. Testing system prompt building...")
        base_prompt = build_dynamic_system_prompt()
        fhyf_prompt = build_dynamic_system_prompt("fhyf_core")
        
        print(f"   Base prompt length: {len(base_prompt)}")
        print(f"   F.H.Y.F. prompt length: {len(fhyf_prompt)}")
        print(f"   Contains F.H.Y.F. content: {'Feel How You Feel' in fhyf_prompt}")
        
        # Test conversation handling
        print("2. Testing conversation handling...")
        response = handle_conversation("hello", "fhyf_core")
        print(f"   Response: {response}")
        
        # Check if response is generic
        generic_indicators = ["How can I assist", "I'm here to help", "What can I do"]
        is_generic = any(indicator in response for indicator in generic_indicators)
        print(f"   Is generic: {is_generic}")
        
        return not is_generic
        
    except Exception as e:
        print(f"❌ Error in conversation flow: {e}")
        return False

def run_component_tests():
    """Run all component tests."""
    print("🔧 DAEMON COMPONENT ISOLATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Mind Module", test_mind_module),
        ("ThreadManager Isolation", test_thread_manager_isolation),
        ("Prompt Content", test_prompt_content),
        ("Conversation Flow", test_conversation_flow)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("COMPONENT TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")

if __name__ == "__main__":
    run_component_tests()
