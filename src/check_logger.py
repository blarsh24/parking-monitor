"""
Check Logger
Maintains a persistent log of all parking checks
"""

import json
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CheckLogger:
    """Log all parking checks to a CSV/JSON file for history"""
    
    def __init__(self, log_file: str = "data/check_history.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist"""
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log_check(self, status: str, price: str, notification_sent: bool = False):
        """
        Log a parking check
        
        Args:
            status: Current parking status
            price: Current price
            notification_sent: Whether a notification was sent
        """
        try:
            # Read existing logs
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Add new entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "price": price,
                "notification_sent": notification_sent,
                "human_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logs.append(entry)
            
            # Keep only last 1000 entries to prevent file from growing too large
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Write back
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            logger.info(f"Check logged: {entry}")
            
            # Also create a simple text log for easy reading
            self._write_simple_log(entry)
            
        except Exception as e:
            logger.error(f"Error logging check: {e}")
    
    def _write_simple_log(self, entry):
        """Write a simple text log that's easy to read"""
        simple_log = Path("data/check_history.txt")
        
        with open(simple_log, 'a') as f:
            status_emoji = "✅" if entry['status'] != 'sold_out' else "❌"
            notif_text = "📨 NOTIFIED" if entry['notification_sent'] else ""
            
            f.write(f"{entry['human_time']} | {status_emoji} {entry['status']} | {entry['price']} {notif_text}\n")
            
            # If status changed to available, add a highlight
            if entry['status'] != 'sold_out':
                f.write(f"{'='*50}\n")
                f.write(f"🎉 PARKING AVAILABLE at {entry['human_time']}!\n")
                f.write(f"{'='*50}\n")
    
    def get_recent_checks(self, limit: int = 10):
        """Get the most recent checks"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            return logs[-limit:] if logs else []
        except:
            return []
    
    def get_last_available_time(self):
        """Find when parking was last available"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            for log in reversed(logs):
                if log['status'] != 'sold_out' and log['status'] != 'unknown':
                    return log['timestamp']
            return None
        except:
            return None