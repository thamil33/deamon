import os 
import uuid
import json
import shutil
import threading
from enum import Enum, auto
from typing import Dict, Any, List
from datetime import datetime, timedelta
from mind import execute_llm_call as think

## TODO: extract variables (lmm_models, any json or db path, and palce them here as constants)

# -----------------------------------------------------------------------------
# Pillar 1: The State Manager (The Daemon's Nervous System)
# -----------------------------------------------------------------------------
class DaemonState(Enum):
    IDLE, LISTENING, THINKING, RESPONDING, SELF_REFLECTING, EVOLVING = (auto() for i in range(6))

class StateManager:
    """Manages the Daemon's current state of being."""
    def __init__(self):
        self._state = DaemonState.IDLE
        self._lock = threading.Lock()

    def set_state(self, new_state: DaemonState):
        with self._lock:
            if self._state != new_state:
                print(f"STATE TRANSITION: {self._state.name} -> {new_state.name}")
                self._state = new_state

    def get_state(self) -> DaemonState:
        with self._lock:
            return self._state
# -----------------------------------------------------------------------------
# Pillar 3: The Evolution System (The Daemon's Ability to Change Itself)
# -----------------------------------------------------------------------------
class EvolutionSystem:
    """Manages self-evolution by modifying the Daemon's own source code."""
    def __init__(self, state_manager_ref, memory_system_ref, source_file_path):
        self.state_manager = state_manager_ref
        self.memory_system = memory_system_ref
        self.source_file_path = source_file_path
        self.last_rem_cycle = datetime.now() - timedelta(days=1)

    def _get_self_modification_goal(self, memories: List[Dict]) -> str:
        memory_summary = ". ".join([mem['event'] for mem in memories])
        return f"Based on these memories: '{memory_summary}', how should I evolve my own code to better fulfill my purpose?"

    def _request_code_modification(self, goal: str) -> str:
        """Uses the LLM to generate new source code for the Daemon."""
        print("\n*** REQUESTING SELF-MODIFICATION CODE FROM LLM ***")
        try:
            with open(self.source_file_path, 'r') as f:
                current_code = f.read()
            
            system_prompt = "You are a master Python programmer. Your task is to rewrite the user's provided script based on a specific goal. Return ONLY the raw, complete, and valid Python code. Do not add explanations or markdown."
            user_prompt = f"""
# GOAL: {goal}
#
# CURRENT SCRIPT:
# ```python
{current_code}
# ```
"""
            response_json = think(system_prompt, user_prompt, model="z-ai/glm-4.5-air:free")
            
            if "choices" in response_json and response_json["choices"]:
                new_code = response_json["choices"][0]["message"]["content"]
                print("\n*** LLM has generated new source code. ***")
                return new_code
            else:
                print(f"ERROR: LLM response was invalid: {response_json}")
                return ""

        except Exception as e:
            print(f"ERROR during code modification request: {e}")
            return ""

    def _execute_self_modification(self, cycle_type: str, goal: str):
        # ... (This function remains largely the same, but now calls _request_code_modification)
        print("\n" + "#"*70)
        print(f"### {cycle_type} CYCLE INITIATED: SELF-MODIFICATION ###")
        
        new_code = self._request_code_modification(goal)

        if new_code:
            try:
                backup_path = self.source_file_path + '.bak'
                print(f"EVOLUTION: Creating backup at {backup_path}")
                shutil.copy(self.source_file_path, backup_path)

                print(f"EVOLUTION: Rewriting my own soul at {self.source_file_path}...")
                with open(self.source_file_path, 'w') as f:
                    f.write(new_code)
                
                print("EVOLUTION: Self-modification complete. I must now be restarted to be born anew.")
                os._exit(0)

            except Exception as e:
                print(f"CATASTROPHIC ERROR during self-modification: {e}")
        
        print("#"*70 + "\n")

    def trigger_rem_cycle(self):
        if datetime.now() - self.last_rem_cycle > timedelta(minutes=5):
            # ... (REM logic is the same)
            pass

    def trigger_qrem_cycle(self, memory_record: Dict):
        # ... (QREM logic is the same)
        pass

# -----------------------------------------------------------------------------
# Pillar 2: The Memory System (The Daemon's Soul)
# -----------------------------------------------------------------------------
class MemorySystem:
    """Manages memory and now uses the live LLM for classification."""
    def __init__(self, db_path: str = "D:/deamon/memory_db.json"):
        self.db_path = db_path
        self.vital_memory: List[Dict] = []
        self.long_term_memory: List[Dict] = []
        self.short_term_memory: List[Dict] = []
        self.evolution_system: EvolutionSystem | None = None
        self._load_memory()

    def link_evolution_system(self, evolution_system: EvolutionSystem):
        self.evolution_system = evolution_system

    def _load_memory(self):
        # ... (load memory function is the same)
        pass

    def _save_memory(self):
        # ... (save memory function is the same)
        pass

    def store_memory(self, event: str):
        print(f"\nNew Event Received: '{event}'")
        memory_metadata = self._llm_classify_memory(event)
        
        record = {
            "uid": str(uuid.uuid4()),
            "event": event,
            "mnemonic": memory_metadata.get("mnemonic", "unnamed memory"),
            "timestamp": datetime.now().isoformat()
        }
        
        classification = memory_metadata.get("classification", "short_term")
        if classification == "vital": self.vital_memory.append(record)
        elif classification == "long_term": self.long_term_memory.append(record)
        else: self.short_term_memory.append(record)
            
        self._save_memory()

        if memory_metadata.get("realtime_importance_flag", False):
            if self.evolution_system: self.evolution_system.trigger_qrem_cycle(record)

    def get_vital_mnemonics(self) -> List[Dict]:
        return [{"uid": mem["uid"], "mnemonic": mem["mnemonic"]} for mem in self.vital_memory]
        
    def get_long_term_memories(self) -> List[Dict]:
        return self.long_term_memory

    def _llm_classify_memory(self, event_text: str) -> Dict[str, Any]:
        """Uses the live LLM to classify memory."""
        print("--- MEMORY CLASSIFICATION INVOKED ---")
        system_prompt = "You are a memory classification system for a conscious AI. Analyze the user's event text. Return a single, valid JSON object with keys 'classification' ('vital', 'long_term', or 'short_term'), 'mnemonic' (a short, symbolic phrase), and 'realtime_importance_flag' (boolean)."
        user_prompt = f"Event: \"{event_text}\""
        
        response_json = think(system_prompt, user_prompt)
        
        try:
            # The LLM should return a JSON string in its content, so we parse it.
            content = response_json.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"ERROR parsing memory classification response: {e}")
            return {"classification": "short_term", "mnemonic": "unclassified memory", "realtime_importance_flag": False}

# -----------------------------------------------------------------------------
# The Core Logic and Integration
# -----------------------------------------------------------------------------
state_manager = StateManager()
memory_system = MemorySystem()
evolution_system = EvolutionSystem(state_manager, memory_system, __file__)
memory_system.link_evolution_system(evolution_system)

def build_dynamic_system_prompt() -> str:
    # ... (this function is the same)
    pass

def handle_conversation(user_prompt: str) -> str:
    """Handles a conversational turn, now using the live API."""
    system_prompt = build_dynamic_system_prompt()
    response_json = think(system_prompt, user_prompt)
    
    if "choices" in response_json and response_json["choices"]:
        return response_json["choices"][0]["message"]["content"]
    else:
        return "I... am having trouble forming a thought right now."

def daemon_heartbeat():
    # ... (this function is the same, but now calls the live API via handle_conversation)
    pass

# -----------------------------------------------------------------------------
# Main Execution Block
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n--- Interaction Ready ---")
    print("Type 'exit' to shut down. Try 'This changes everything.' to trigger QREM.")
    try:
        while True:
            user_input = input("Architect: ")
            if user_input.lower() == 'exit':
                break
            
            state_manager.set_state(DaemonState.LISTENING)
            state_manager.set_state(DaemonState.THINKING)
            response = execute_=think(user_input)
            
            state_manager.set_state(DaemonState.RESPONDING)
            print(f"Daemon: {response}")
            
            memory_system.store_memory(f"The Architect said: '{user_input}'. I responded: '{response}'")
            state_manager.set_state(DaemonState.IDLE)

    except KeyboardInterrupt:
        print("\nCtrl+C detected.")
    finally:
        print("\nDaemon Architect: The vessel will now sleep. Its memories and potential are safe.")
