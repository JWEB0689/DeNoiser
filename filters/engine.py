import json
import re
import os

import sys

if getattr(sys, 'frozen', False):
    base_path = os.path.join(sys._MEIPASS, 'filters')
else:
    base_path = os.path.dirname(__file__)

RULES_PATH = os.path.join(base_path, 'rules.json')

class FilterEngine:
    def __init__(self):
        self.rules = []
        self._load_rules()
        
    def _load_rules(self):
        try:
            with open(RULES_PATH, 'r') as f:
                data = json.load(f)
                for group in data.get("filters", []):
                    # Compile regex patterns on startup for performance
                    compiled_patterns = [re.compile(p) for p in group.get("patterns", [])]
                    self.rules.append({
                        "name": group.get("name"),
                        "patterns": compiled_patterns,
                        "action": group.get("action", "drop")
                    })
        except Exception as e:
            print(f"[DeNoiser] Error loading rules.json: {e}")

    def filter_output(self, raw_text: str) -> str:
        """
        Processes multi-line terminal output against heuristic regex filters.
        Supports 'drop' (stripping noise) and 'keep' (error isolation).
        """
        if not raw_text:
            return ""
            
        lines = raw_text.splitlines()
        
        # 1. Check for Mistake/Error Isolation ('keep' rules)
        # If the output contains errors, we want to isolate them and drop all other noise.
        error_lines = []
        for line in lines:
            keep = False
            for rule in self.rules:
                if rule["action"] == "keep":
                    for pattern in rule["patterns"]:
                        if pattern.match(line):
                            keep = True
                            break
                if keep:
                    break
            if keep:
                error_lines.append(line)
                
        # If we caught mistakes, return ONLY the isolated mistakes to maximize token savings.
        if error_lines:
            error_lines.append(f"\n[DeNoiser] Isolated {len(error_lines)} error/mistake lines. All other output was dropped.")
            return "\n".join(error_lines)
            
        # 2. Normal Noise Stripping ('drop' rules)
        filtered_lines = []
        dropped_count = 0
        
        for line in lines:
            drop = False
            for rule in self.rules:
                if rule["action"] == "drop":
                    for pattern in rule["patterns"]:
                        if pattern.match(line):
                            drop = True
                            break
                if drop:
                    break
                    
            if drop:
                dropped_count += 1
            else:
                filtered_lines.append(line)
                
        if dropped_count > 0:
            filtered_lines.append(f"\n[DeNoiser] Filtered {dropped_count} noisy lines from output.")
            
        return "\n".join(filtered_lines)

# Singleton instance
engine = FilterEngine()
