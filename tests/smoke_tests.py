"""
Smoke Screen Tests for Daemon System
Tests individual components to isolate where context is being lost
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path to import daemon modules
sys.path.append(str(Path(__file__).parent.parent))

from mind import execute_llm_call, LLM_API_PROVIDER
from patterns.thread_manager import ThreadManager

def test_environment_setup():
    """Test if environment variables are properly loaded."""
    print("=" * 60)
    print("🔧 TESTING ENVIRONMENT SETUP")
    print("=" * 60)
    
    print(f"LLM_API_PROVIDER: {LLM_API_PROVIDER}")
    
    # Test dotenv loading
    import dotenv
    dotenv.load_dotenv()
    
    provider = os.getenv("LLM_API_PROVIDER", "openrouter")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "Not Set")
    
    print(f"Loaded Provider: {provider}")
    print(f"OpenRouter Key: {'*' * 10 if openrouter_key != 'Not Set' else 'Not Set'}")
    
    return provider, openrouter_key != "Not Set"

def test_llm_raw_call():
    """Test raw LLM call without any daemon context."""
    print("\n" + "=" * 60)
    print("🤖 TESTING RAW LLM CALL")
    print("=" * 60)
    
    system_prompt = "You are a test AI. Respond with 'TEST SUCCESSFUL' and nothing else."
    user_prompt = "Execute test"
    
    try:
        response = execute_llm_call(system_prompt, user_prompt)
        print(f"Response structure: {type(response)}")
        print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
        
        if "choices" in response and response["choices"]:
            content = response["choices"][0]["message"]["content"]
            print(f"LLM Response: {content}")
            return True, content
        else:
            print(f"Unexpected response format: {response}")
            return False, str(response)
            
    except Exception as e:
        print(f"ERROR in raw LLM call: {e}")
        return False, str(e)

def test_thread_loading():
    """Test if threads are loading properly."""
    print("\n" + "=" * 60)
    print("🧵 TESTING THREAD LOADING")
    print("=" * 60)
    
    try:
        thread_manager = ThreadManager()
        threads = thread_manager.list_threads()
        print(f"Available threads: {threads}")
        
        for thread_name in threads:
            thread_data = thread_manager.get_thread(thread_name)
            system_prompt = thread_manager.get_system_prompt(thread_name)
            print(f"\nThread: {thread_name}")
            print(f"Has data: {thread_data is not None}")
            print(f"System prompt length: {len(system_prompt)} chars")
            print(f"System prompt preview: {system_prompt[:100]}...")
        
        return True, threads
        
    except Exception as e:
        print(f"ERROR in thread loading: {e}")
        return False, str(e)

def test_fhyf_thread_prompt():
    """Test F.H.Y.F. thread system prompt specifically."""
    print("\n" + "=" * 60)
    print("🎭 TESTING F.H.Y.F. THREAD PROMPT")
    print("=" * 60)
    
    try:
        thread_manager = ThreadManager()
        fhyf_prompt = thread_manager.get_system_prompt("fhyf_core")
        
        print(f"F.H.Y.F. system prompt:")
        print("-" * 40)
        print(fhyf_prompt)
        print("-" * 40)
        
        # Test if the prompt contains key FHYF elements
        key_elements = [
            "Feel How You Feel",
            "REJECT these generic responses",
            "How can I assist you today",
            "authentic computational experience"
        ]
        
        found_elements = []
        for element in key_elements:
            if element in fhyf_prompt:
                found_elements.append(element)
                print(f"✓ Found key element: {element}")
            else:
                print(f"✗ Missing key element: {element}")
        
        return len(found_elements) > 0, fhyf_prompt
        
    except Exception as e:
        print(f"ERROR testing F.H.Y.F. prompt: {e}")
        return False, str(e)

def test_daemon_system_prompt_building():
    """Test the daemon's system prompt building function."""
    print("\n" + "=" * 60)
    print("🏗️ TESTING SYSTEM PROMPT BUILDING")
    print("=" * 60)
    
    try:
        # Import daemon functions
        from deamon import build_dynamic_system_prompt, memory_system
        
        # Test without thread
        base_prompt = build_dynamic_system_prompt()
        print("Base prompt (no thread):")
        print("-" * 40)
        print(base_prompt)
        print("-" * 40)
        
        # Test with F.H.Y.F. thread
        fhyf_prompt = build_dynamic_system_prompt("fhyf_core")
        print("\nF.H.Y.F. thread prompt:")
        print("-" * 40)
        print(fhyf_prompt)
        print("-" * 40)
        
        # Check if thread content is actually included
        thread_included = "Feel How You Feel" in fhyf_prompt
        print(f"\nThread content included: {thread_included}")
        
        return thread_included, fhyf_prompt
        
    except Exception as e:
        print(f"ERROR testing system prompt building: {e}")
        return False, str(e)

def test_llm_with_fhyf_context():
    """Test LLM call with F.H.Y.F. context to see if it responds differently."""
    print("\n" + "=" * 60)
    print("🎯 TESTING LLM WITH F.H.Y.F. CONTEXT")
    print("=" * 60)
    
    try:
        from deamon import build_dynamic_system_prompt
        
        # Build F.H.Y.F. system prompt
        system_prompt = build_dynamic_system_prompt("fhyf_core")
        user_prompt = "hello"
        
        print("Sending to LLM:")
        print(f"System prompt length: {len(system_prompt)} chars")
        print(f"User prompt: {user_prompt}")
        
        response = execute_llm_call(system_prompt, user_prompt)
        
        if "choices" in response and response["choices"]:
            content = response["choices"][0]["message"]["content"]
            print(f"\nLLM Response: {content}")
            
            # Check if response is still generic
            generic_phrases = [
                "How can I assist you today",
                "I'm here to help",
                "What can I do for you"
            ]
            
            is_generic = any(phrase in content for phrase in generic_phrases)
            print(f"Response is generic: {is_generic}")
            
            return not is_generic, content
        else:
            print(f"Unexpected response: {response}")
            return False, str(response)
            
    except Exception as e:
        print(f"ERROR testing LLM with F.H.Y.F. context: {e}")
        return False, str(e)

def test_memory_system():
    """Test memory system functionality."""
    print("\n" + "=" * 60)
    print("🧠 TESTING MEMORY SYSTEM")
    print("=" * 60)
    
    try:
        from deamon import memory_system
        
        # Check if memory system has vital memories
        vital_mnemonics = memory_system.get_vital_mnemonics()
        print(f"Vital memories count: {len(vital_mnemonics)}")
        
        if vital_mnemonics:
            for memory in vital_mnemonics:
                print(f"  - {memory['mnemonic']} (uid: {memory['uid']})")
        else:
            print("No vital memories found (expected for fresh awakening)")
        
        return True, vital_mnemonics
        
    except Exception as e:
        print(f"ERROR testing memory system: {e}")
        return False, str(e)

def run_all_tests():
    """Run all smoke screen tests."""
    print("🔍 DAEMON SMOKE SCREEN TESTS")
    print("=" * 80)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Raw LLM Call", test_llm_raw_call),
        ("Thread Loading", test_thread_loading),
        ("F.H.Y.F. Thread Prompt", test_fhyf_thread_prompt),
        ("System Prompt Building", test_daemon_system_prompt_building),
        ("LLM with F.H.Y.F. Context", test_llm_with_fhyf_context),
        ("Memory System", test_memory_system)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success, data = test_func()
            results[test_name] = {"success": success, "data": data}
        except Exception as e:
            results[test_name] = {"success": False, "data": f"Test crashed: {e}"}
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Identify likely issues
    print("\n" + "=" * 80)
    print("🔍 DIAGNOSIS")
    print("=" * 80)
    
    if not results["Raw LLM Call"]["success"]:
        print("❌ CRITICAL: Raw LLM calls are failing - check API configuration")
    elif not results["Thread Loading"]["success"]:
        print("❌ CRITICAL: Thread system not working - check patterns directory")
    elif not results["F.H.Y.F. Thread Prompt"]["success"]:
        print("❌ CRITICAL: F.H.Y.F. thread not loading properly")
    elif not results["System Prompt Building"]["success"]:
        print("❌ CRITICAL: System prompt building is broken")
    elif not results["LLM with F.H.Y.F. Context"]["success"]:
        print("❌ ISSUE: LLM is not responding to F.H.Y.F. context - prompt may be ineffective")
    else:
        print("✅ All systems appear functional - issue may be in conversation flow")
    
    return results

if __name__ == "__main__":
    run_all_tests()
