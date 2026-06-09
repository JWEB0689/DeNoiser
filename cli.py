import sys
import subprocess
from filters.engine import engine

VERSION = "v1.1.0"

def print_usage():
    print("Usage: denoiser <command> [args...]")
    print("\nMeta-commands:")
    print("  denoiser version   : Show the current version.")
    print("  denoiser list      : List all loaded TOML filter rules.")
    print("  denoiser test      : Run a built-in diagnostic test to verify filtering.")
    print("  denoiser discover  : Scan local AI agent transcripts to find unfiltered noisy commands.")
    print("  denoiser hook      : Generate and install shell wrappers to automatically intercept AI commands.")
    print("\nExample: denoiser git status")

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
        
    command = sys.argv[1:]
    
    # Native Meta-Command Interception
    if command[0] == "version":
        print("DeNoiser v1.3.1")
        sys.exit(0)
    elif command[0] == "list":
        print(f"--- Loaded DeNoiser Filters ({len(engine.filters)}) ---")
        for f in engine.filters:
            print(f"[{f['id']}] -> matches '{f['match_command'].pattern}'")
        sys.exit(0)
    elif command[0] == "test":
        print("Running DeNoiser native diagnostic test...")
        fake_command = "npm install fake-package"
        fake_output = (
            "npm WARN deprecated fake-package@1.0.0: this package is deprecated\n"
            "added 42 packages, and audited 43 packages in 3s\n"
            "found 0 vulnerabilities\n"
            "Successfully installed fake-package!\n"
        )
        print("\n--- RAW OUTPUT (What LLM normally sees) ---")
        print(fake_output.strip())
        print("\n--- FILTERED OUTPUT (What LLM actually sees) ---")
        filtered = engine.filter_output(fake_command, fake_output)
        print(filtered)
        sys.exit(0)
    elif command[0] == "discover":
        try:
            from discover import run_discover
            run_discover()
        except ImportError:
            print("[DeNoiser] Error: discover module not found.")
        sys.exit(0)
    elif command[0] == "hook":
        try:
            from hook import run_hook
            run_hook()
        except ImportError:
            print("[DeNoiser] Error: hook module not found.")
        sys.exit(0)
    
    try:
        # Execute the raw command, merging stderr into stdout for complete filtering
        # We use shell=True to allow Windows built-in commands (like 'echo' or 'dir')
        result = subprocess.run(command, capture_output=True, text=True, check=False, shell=True)
        raw_output = result.stdout + (result.stderr if result.stderr else "")
        
        command_str = " ".join(command)
        # Pass the massive output bloat into the DeNoiser
        filtered_output = engine.filter_output(command_str, raw_output)
        
        # Print the beautifully optimized result back to the user
        print(filtered_output)
        
        # Ensure we return the same exit code as the wrapped command
        sys.exit(result.returncode)
        
    except FileNotFoundError:
        print(f"[DeNoiser] Error: Command '{command[0]}' not found.")
        sys.exit(127)
    except Exception as e:
        print(f"[DeNoiser] Interceptor Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
