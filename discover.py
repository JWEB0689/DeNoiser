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
                                        cmd = cmd.strip('"')
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

def split_chained_commands(cmd: str) -> List[str]:
    """Split a chained command string into individual commands.
    
    Handles: && , || , ; , and | (pipe) separators.
    For pipes, extracts each command in the pipeline individually.
    """
    # Split on && , || , ;
    parts = re.split(r'\s*(?:&&|\|\||;)\s*', cmd)
    
    individual = []
    for part in parts:
        # Further split on pipes to get individual pipeline stages
        pipe_parts = re.split(r'\s*\|\s*', part)
        individual.extend(pipe_parts)
    
    return [p.strip() for p in individual if p.strip()]

def simplify_command(cmd: str) -> str:
    """Extracts the base executable name from a command string.
    
    Strips environment variable prefixes, sudo, and resolves
    the first real command token.
    """
    cmd = cmd.strip()
    
    # Strip leading env var assignments (e.g., FOO=bar command)
    cmd = re.sub(r'^(?:[A-Z_]+=[^\s]+\s+)+', '', cmd)
    
    # Strip sudo
    cmd = re.sub(r'^sudo\s+', '', cmd)
    
    # Strip cd ... && prefix (very common in agent commands)
    cmd = re.sub(r'^cd\s+[^\s;&]+\s*(?:&&\s*)?', '', cmd)
    
    parts = cmd.split()
    
    if not parts:
        return "unknown"
        
    base = parts[0]
    
    # Strip path prefixes (e.g., /usr/bin/git -> git, ./gradlew -> gradlew)
    base = os.path.basename(base)
    
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
    
    for raw_cmd in all_cmds:
        # Split chained commands so each part is evaluated independently
        individual_cmds = split_chained_commands(raw_cmd)
        
        for cmd in individual_cmds:
            base_cmd = simplify_command(cmd)
            
            matched = False
            for f in engine.filters:
                # Skip fallback — we want to know explicit tool coverage
                if f["id"] == "fallback":
                    continue
                if f["match_command"].search(cmd) or f["match_command"].search(base_cmd):
                    matched = True
                    break
                    
            if matched:
                filtered_count += 1
            else:
                unfiltered_counts[base_cmd] += 1
            
    total_individual = filtered_count + sum(unfiltered_counts.values())
    coverage = (filtered_count / total_individual) * 100 if total_individual > 0 else 0
    
    print(f"Total Commands Analyzed: {total_individual} (from {len(all_cmds)} raw entries)")
    print(f"Commands Protected by DeNoiser: {filtered_count} ({coverage:.1f}% Coverage)\n")
    
    print("Top 10 Unfiltered Targets (Write TOML rules for these!):")
    if not unfiltered_counts:
        print("Amazing! 100% of your commands are explicitly covered by DeNoiser filters!")
    else:
        for cmd, count in unfiltered_counts.most_common(10):
            print(f"  - `{cmd}` ({count} times)")
            
    print("-" * 50)
