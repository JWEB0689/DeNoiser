import os
import sys
import platform
import re
import subprocess
from filters.engine import engine

HOOK_START = "# --- DeNoiser Auto-Intercept Hooks Start ---"
HOOK_END = "# --- DeNoiser Auto-Intercept Hooks End ---"

def extract_base_commands():
    cmds = []
    for f in engine.filters:
        if f["id"] == "fallback" or ".*" in f["match_command"].pattern:
            continue
        # Extract command from regex pattern like '^npm\b'
        pattern = f["match_command"].pattern
        # Naive extraction: take letters/numbers/hyphens from the start
        match = re.search(r'\^?([a-zA-Z0-9_-]+)', pattern)
        if match:
            cmds.append(match.group(1))
    return sorted(list(set(cmds)))

def generate_powershell_hooks(commands):
    lines = [HOOK_START]
    for cmd in commands:
        lines.append(f"function {cmd} {{ denoiser {cmd} $args }}")
    lines.append(HOOK_END)
    return "\n".join(lines)

def generate_bash_hooks(commands):
    lines = [HOOK_START]
    for cmd in commands:
        lines.append(f"{cmd}() {{ denoiser {cmd} \"$@\"; }}")
    lines.append(HOOK_END)
    return "\n".join(lines)

def get_powershell_profile():
    try:
        # Ask PowerShell for the CurrentUserCurrentHost profile path
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Write-Output $PROFILE"], 
            capture_output=True, text=True, check=True
        )
        path = result.stdout.strip()
        if path:
            return path
    except Exception:
        pass
    
    # Fallback if powershell command fails
    home = os.path.expanduser("~")
    ps_dir = os.path.join(home, "Documents", "WindowsPowerShell")
    return os.path.join(ps_dir, "Microsoft.PowerShell_profile.ps1")

def patch_file(filepath, hook_content):
    if not os.path.exists(filepath):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                pass
        except Exception as e:
            print(f"[DeNoiser] Could not create {filepath}: {e}")
            return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        content = ""

    # Remove old hooks if they exist
    if HOOK_START in content and HOOK_END in content:
        start_idx = content.find(HOOK_START)
        end_idx = content.find(HOOK_END) + len(HOOK_END)
        content = content[:start_idx] + content[end_idx:]

    content = content.strip() + "\n\n" + hook_content + "\n"

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip() + "\n")
        print(f"[OK] Successfully installed hooks into: {filepath}")
    except Exception as e:
        print(f"[DeNoiser] Failed to write to {filepath}: {e}")

def run_hook():
    cmds = extract_base_commands()
    if not cmds:
        print("[DeNoiser] No specific tool filters found in builtin.toml to hook.")
        return

    print(f"Installing DeNoiser hooks for: {', '.join(cmds)}\n")

    if platform.system() == "Windows":
        profile_path = get_powershell_profile()
        hook_content = generate_powershell_hooks(cmds)
        patch_file(profile_path, hook_content)
        print("\nRestart your PowerShell terminal or run `. $PROFILE` to apply.")
    else:
        home = os.path.expanduser("~")
        bash_profile = os.path.join(home, ".bashrc")
        zsh_profile = os.path.join(home, ".zshrc")
        
        hook_content = generate_bash_hooks(cmds)
        patched = False
        
        if os.path.exists(bash_profile):
            patch_file(bash_profile, hook_content)
            patched = True
            
        if os.path.exists(zsh_profile) or not patched:
            patch_file(zsh_profile, hook_content)
            
        print("\nRestart your terminal or run `source ~/.bashrc` (or ~/.zshrc) to apply.")

if __name__ == "__main__":
    run_hook()
