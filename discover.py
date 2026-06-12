import os
import glob
import json
import re
from collections import Counter
from typing import List

from filters.engine import engine

def extract_antigravity_commands() -> List[str]:
    home = os.path.expanduser("~")
    # Matches ~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl
    pattern = os.path.join(home, ".gemini", "antigravity-ide", "brain", "*", ".system_generated", "logs", "transcript.jsonl")
    
    commands = []
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if '"run_command"' in line:
                        try:
                            data = json.loads(line)
                            tool_calls = data.get("tool_calls", [])
                            if tool_calls is None:
                                continue
                            for call in tool_calls:
                                if call.get("name") == "run_command":
                                    args = call.get("args", {})
                                    cmd = args.get("CommandLine")
                                    if cmd:
                                        commands.append(cmd)
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
    return commands

def extract_claude_commands() -> List[str]:
    home = os.path.expanduser("~")
    projects_dir = os.path.join(home, ".claude", "projects")
    commands = []
    
    if not os.path.exists(projects_dir):
        return commands
        
    for root, dirs, files in os.walk(projects_dir):
        for file in files:
            if file.endswith(".jsonl"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            if '"Bash"' in line and '"tool_use"' in line:
                                try:
                                    data = json.loads(line)
                                    msg = data.get("message", {})
                                    content = msg.get("content", [])
                                    if isinstance(content, list):
                                        for block in content:
                                            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                                                cmd = block.get("input", {}).get("command")
                                                if cmd:
                                                    commands.append(cmd)
                                except json.JSONDecodeError:
                                    continue
                except Exception:
                    pass
    return commands

def simplify_command(cmd: str) -> str:
    """Extracts the base executable name (e.g. 'git commit -m' -> 'git')"""
    cmd = re.sub(r'^[A-Z_]+=[^\s]+\s+', '', cmd.strip())
    cmd = cmd.replace("sudo ", "")
    parts = cmd.split()
    
    if not parts:
        return "unknown"
        
    base = parts[0]
    
    # Check for chained commands
    if "&&" in cmd or "|" in cmd or ";" in cmd:
        return "chained_commands (complex)"
        
    return base

def run_discover():
    print("Discovering local AI agent transcripts...")
    ag_cmds = extract_antigravity_commands()
    claude_cmds = extract_claude_commands()
    
    all_cmds = ag_cmds + claude_cmds
    print(f"Found {len(ag_cmds)} commands from Antigravity IDE")
    print(f"Found {len(claude_cmds)} commands from Claude Code")
    print("-" * 50)
    
    if not all_cmds:
        print("No commands found in logs. Start using your agents to gather data!")
        return

    filtered_count = 0
    unfiltered_counts = Counter()
    
    for cmd in all_cmds:
        matched = False
        for f in engine.filters:
            # Prevent fallback rule from padding the stats, we want to know explicit tool coverage
            if f["id"] == "fallback":
                continue
            if f["match_command"].search(cmd):
                matched = True
                break
                
        if matched:
            filtered_count += 1
        else:
            base_cmd = simplify_command(cmd)
            unfiltered_counts[base_cmd] += 1
            
    total = len(all_cmds)
    coverage = (filtered_count / total) * 100 if total > 0 else 0
    
    print(f"Total Commands Executed: {total}")
    print(f"Commands Protected by DeNoiser: {filtered_count} ({coverage:.1f}% Coverage)\n")
    
    print("Top 5 Unfiltered Targets (Write TOML rules for these!):")
    if not unfiltered_counts:
        print("Amazing! 100% of your commands are explicitly covered by DeNoiser filters!")
    else:
        for cmd, count in unfiltered_counts.most_common(5):
            print(f"  - `{cmd}` ({count} times)")
            
    print("-" * 50)
