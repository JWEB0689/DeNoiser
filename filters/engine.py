import json
import re
import os

RULES_PATH = os.path.join(os.path.dirname(__file__), 'rules.json')

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
            print(f"[RTK Engine] Error loading rules.json: {e}")

    def filter_output(self, raw_text: str) -> str:
        """
        Processes multi-line terminal output against heuristic regex filters.
        Drops lines that match noise patterns to compress tokens.
        """
        if not raw_text:
            return ""
            
        lines = raw_text.splitlines()
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
                
        # Optional: Add a truncation notice if we dropped lines
        if dropped_count > 0:
            filtered_lines.append(f"\n[RTK Engine] Filtered {dropped_count} noisy lines from output.")
            
        return "\n".join(filtered_lines)

# Singleton instance
engine = FilterEngine()
