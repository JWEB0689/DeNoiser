import sys
import os
import re

# Use tomllib from Python 3.11+
try:
    import tomllib
except ImportError:
    import tomli as tomllib

if getattr(sys, 'frozen', False):
    base_path = os.path.join(sys._MEIPASS, 'filters')
else:
    base_path = os.path.dirname(__file__)

RULES_PATH = os.path.join(base_path, 'builtin.toml')

class FilterEngine:
    def __init__(self):
        self.filters = []
        self._load_rules()
        
    def _load_rules(self):
        try:
            with open(RULES_PATH, 'rb') as f:
                data = tomllib.load(f)
                
            for filter_id, config in data.get("filters", {}).items():
                compiled_match = re.compile(config.get("match_command", ".*"))
                
                # Compile regex lists
                strip_lines = [re.compile(p) for p in config.get("strip_lines_matching", [])]
                keep_lines = [re.compile(p) for p in config.get("keep_lines_matching", [])]
                
                # Replace rules
                replace_rules = []
                for rule in config.get("replace", []):
                    if "pattern" in rule and "replacement" in rule:
                        replace_rules.append((re.compile(rule["pattern"]), rule["replacement"]))
                
                # Match output rules
                match_output = []
                for rule in config.get("match_output", []):
                    if "pattern" in rule and "message" in rule:
                        match_output.append((re.compile(rule["pattern"]), rule["message"]))
                        
                self.filters.append({
                    "id": filter_id,
                    "match_command": compiled_match,
                    "strip_ansi": config.get("strip_ansi", False),
                    "strip_lines_matching": strip_lines,
                    "keep_lines_matching": keep_lines,
                    "replace": replace_rules,
                    "match_output": match_output,
                    "truncate_lines_at": config.get("truncate_lines_at"),
                    "tail_lines": config.get("tail_lines"),
                    "max_lines": config.get("max_lines"),
                    "on_empty": config.get("on_empty")
                })
        except Exception as e:
            print(f"[DeNoiser] Error loading builtin.toml: {e}")

    def _strip_ansi(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def filter_output(self, command: str, raw_text: str) -> str:
        """
        Executes the 8-stage RTK TOML filtering pipeline.
        """
        if not raw_text:
            return ""
            
        # 1. Match Command
        active_filter = None
        for f in self.filters:
            if f["match_command"].search(command):
                active_filter = f
                break
                
        if not active_filter:
            return raw_text # Pass through if no filter matches
            
        # 2. Strip ANSI
        if active_filter["strip_ansi"]:
            raw_text = self._strip_ansi(raw_text)
            
        lines = raw_text.splitlines()
        
        # 3. Replace
        for pattern, replacement in active_filter["replace"]:
            lines = [pattern.sub(replacement, line) for line in lines]
            
        # 4. Match Output (Short-circuit)
        for pattern, message in active_filter["match_output"]:
            for line in lines:
                if pattern.search(line):
                    return message
                    
        # 5. Strip / Keep Lines
        filtered_lines = []
        dropped_count = 0
        kept_count = 0
        
        has_keep_rules = len(active_filter["keep_lines_matching"]) > 0
        
        for line in lines:
            drop = False
            keep = False
            
            # Check keep rules first
            for pattern in active_filter["keep_lines_matching"]:
                if pattern.search(line):
                    keep = True
                    break
                    
            if not keep:
                # Check drop rules
                for pattern in active_filter["strip_lines_matching"]:
                    if pattern.search(line):
                        drop = True
                        break
                        
            if has_keep_rules:
                if keep:
                    filtered_lines.append(line)
                    kept_count += 1
                else:
                    dropped_count += 1
            else:
                if drop:
                    dropped_count += 1
                else:
                    filtered_lines.append(line)
                    
        # 6. Truncate
        truncate_at = active_filter["truncate_lines_at"]
        if truncate_at is not None and truncate_at > 0:
            filtered_lines = [line[:truncate_at] + "..." if len(line) > truncate_at else line for line in filtered_lines]
            
        # 7. Tail lines
        tail = active_filter["tail_lines"]
        if tail is not None and tail > 0:
            filtered_lines = filtered_lines[-tail:]
            
        # 8. Max lines
        max_len = active_filter["max_lines"]
        if max_len is not None and max_len > 0:
            filtered_lines = filtered_lines[:max_len]
            
        # 9. On Empty
        if not filtered_lines and active_filter["on_empty"]:
            return active_filter["on_empty"]
            
        # Append stats
        if dropped_count > 0 or kept_count > 0:
            action_str = f"Filtered {dropped_count} noisy lines" if not has_keep_rules else f"Isolated {kept_count} lines"
            filtered_lines.append(f"\n[DeNoiser] {action_str} using '{active_filter['id']}' filter.")
            
        return "\n".join(filtered_lines)

# Singleton instance
engine = FilterEngine()
