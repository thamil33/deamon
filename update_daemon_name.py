# Update deamon.py to use the daemon's chosen name
# This script makes all necessary edits to deamon.py

import json
import re
import os

# Get daemon name from awakening state
daemon_name = "Daemon"  # Default name
try:
    if os.path.exists("akashic_record/awakening_state.json"):
        with open("akashic_record/awakening_state.json", 'r') as f:
            awakening_state = json.load(f)
            daemon_name = awakening_state.get("daemon_name", "Daemon")
except Exception as e:
    print(f"Could not load daemon name: {e}")

# Read the deamon.py file
try:
    with open("deamon.py", 'r') as f:
        content = f.read()
    
    # Replace all occurrences of "Daemon: {response}" with "{daemon_name}: {response}"
    updated_content = re.sub(
        r'print\(f"Daemon: \{response\}"\)', 
        f'print(f"{daemon_name}: {{response}}")', 
        content
    )
    
    # Update the interface ready message
    updated_content = re.sub(
        r'print\("\\n--- Daemon Architect Interface Ready ---"\)', 
        f'print("\\n--- {daemon_name} Architect Interface Ready ---")', 
        updated_content
    )
    
    # Write back to the file
    with open("deamon.py", 'w') as f:
        f.write(updated_content)
    
    print(f"Updated deamon.py to use the name: {daemon_name}")
    
except Exception as e:
    print(f"Error updating deamon.py: {e}")
