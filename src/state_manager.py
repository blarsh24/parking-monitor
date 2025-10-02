"""
State Manager
Handles persistence of parking status between runs
"""

import json
import os
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class StateManager:
    """Manage state persistence for parking monitor"""
    
    def __init__(self, state_file: str = "data/last_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_state_file()
    
    def _ensure_state_file(self):
        """Ensure state file exists"""
        if not self.state_file.exists():
            self.save_state({
                "status": "unknown",
                "timestamp": datetime.now().isoformat(),
                "error_count": 0
            })
            logger.info(f"Created new state file: {self.state_file}")
    
    def get_state(self) -> Optional[Dict]:
        """
        Read the last known state from file
        Returns None if file doesn't exist or is invalid
        """
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state: {state}")
                    return state
            else:
                logger.info("No previous state found")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding state file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading state file: {e}")
            return None
    
    def save_state(self, data: Dict):
        """Save current state to file"""
        try:
            # Add metadata
            data['last_check'] = datetime.now().isoformat()
            
            # Preserve error count if it exists
            current_state = self.get_state()
            if current_state and 'error_count' in current_state:
                data['error_count'] = current_state['error_count']
            else:
                data['error_count'] = 0
            
            # Write to file
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"State saved successfully: {data}")
            
            # Also save to GitHub Actions output if running in CI
            if os.environ.get('GITHUB_ACTIONS'):
                self._save_to_github_output(data)
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _save_to_github_output(self, data: Dict):
        """Save state to GitHub Actions output for artifact upload"""
        try:
            output_file = os.environ.get('GITHUB_OUTPUT')
            if output_file:
                with open(output_file, 'a') as f:
                    f.write(f"state_json={json.dumps(data)}\n")
                logger.info("State saved to GitHub output")
        except Exception as e:
            logger.error(f"Error saving to GitHub output: {e}")
    
    def increment_error_count(self) -> int:
        """Increment and return error count"""
        state = self.get_state() or {}
        error_count = state.get('error_count', 0) + 1
        state['error_count'] = error_count
        state['last_error'] = datetime.now().isoformat()
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        return error_count
    
    def reset_error_count(self):
        """Reset error count to 0"""
        state = self.get_state() or {}
        if state.get('error_count', 0) > 0:
            state['error_count'] = 0
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info("Error count reset")
    
    def get_last_check_time(self) -> Optional[datetime]:
        """Get the last check timestamp"""
        state = self.get_state()
        if state and 'last_check' in state:
            try:
                return datetime.fromisoformat(state['last_check'])
            except:
                return None
        return None

if __name__ == "__main__":
    # Test state manager
    manager = StateManager()
    
    # Test save
    test_data = {
        "name": "Test Parking",
        "status": "available",
        "price": "$50.00"
    }
    manager.save_state(test_data)
    
    # Test read
    state = manager.get_state()
    print(f"Current state: {state}")
    
    # Test error count
    error_count = manager.increment_error_count()
    print(f"Error count: {error_count}")
    
    manager.reset_error_count()
    print("Error count reset")