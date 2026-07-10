import os
import sys
import platform
import re
import subprocess
from filters.engine import engine

HOOK_START = "# --- DeNoiser Auto-Intercept Hooks Start ---"
HOOK_END = "# --- DeNoiser Auto-Intercept Hooks End ---"

# Filters that only make sense on specific platforms
WINDOWS_ONLY_FILTERS = {"winget", "powershell"}
UNIX_ONLY_FILTERS = {"brew"}

def extract_base_commands():
    """Extract hookable command names from loaded TOML filters,
    skipping platform-irrelevant and catch-all filters."""
    is_windows = platform.system() == "Windows"
    skip_filters = UNIX_ONLY_FILTERS if is_windows else WINDOWS_ONLY_FILTERS
    
    cmds = []
    for f in engine.filters:
        filter_id = f["id"]
        
        # Skip catch-all filters
        if filter_id == "fallback" or ".*" in f["match_command"].pattern:
            continue
        
        # Skip platform-irrelevant filters
        if filter_id in skip_filters:
            continue
            
        # Extract command name from regex pattern like '^npm\b'
        pattern = f["match_command"].pattern
        match = re.search(r'\^?([a-zA-Z0-9_-]+)', pattern)
        if match:
            cmd_name = match.group(1)
            # Sanity check: skip names that are clearly not CLI commands
            if len(cmd_name) > 1 and cmd_name.isascii():
                cmds.append(cmd_name)
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
        lines.append(f'{cmd}() {{ denoiser {cmd} "$@"; }}')
    lines.append(HOOK_END)
    return "\n".join(lines)

def get_powershell_profile():
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Write-Output $PROFILE"], 
            capture_output=True, text=True, check=True
        )
        path = result.stdout.strip()
        if path:
            return path
    except Exception:
        pass
    
    home = os.path.expanduser("~")
    ps_dir = os.path.join(home, "Documents", "WindowsPowerShell")
    return os.path.join(ps_dir, "Microsoft.PowerShell_profile.ps1")

def patch_file(filepath, hook_content, dry_run=False):
    """Patch a shell profile file with DeNoiser hooks."""
    if dry_run:
        print(f"\n[DRY-RUN] Would write to: {filepath}")
        print(f"[DRY-RUN] Content:\n{hook_content}")
        return
    
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

def run_hook(dry_run=False):
    cmds = extract_base_commands()
    if not cmds:
        print("[DeNoiser] No specific tool filters found in builtin.toml to hook.")
        return

    mode_label = " (DRY-RUN)" if dry_run else ""
    print(f"Installing DeNoiser hooks{mode_label} for: {', '.join(cmds)}\n")

    if platform.system() == "Windows":
        profile_path = get_powershell_profile()
        hook_content = generate_powershell_hooks(cmds)
        patch_file(profile_path, hook_content, dry_run=dry_run)
        if not dry_run:
            print("\nRestart your PowerShell terminal or run `. $PROFILE` to apply.")
    else:
        home = os.path.expanduser("~")
        bash_profile = os.path.join(home, ".bashrc")
        zsh_profile = os.path.join(home, ".zshrc")
        
        hook_content = generate_bash_hooks(cmds)
        patched = False
        
        if os.path.exists(bash_profile):
            patch_file(bash_profile, hook_content, dry_run=dry_run)
            patched = True
            
        if os.path.exists(zsh_profile) or not patched:
            patch_file(zsh_profile, hook_content, dry_run=dry_run)
            
        if not dry_run:
            print("\nRestart your terminal or run `source ~/.bashrc` (or ~/.zshrc) to apply.")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_hook(dry_run=dry_run)
