import sys
import subprocess
from filters.engine import engine

def main():
    if len(sys.argv) < 2:
        print("Usage: denoiser <command> [args...]")
        print("Example: denoiser git status")
        sys.exit(1)
        
    command = sys.argv[1:]
    
    try:
        # Execute the raw command, merging stderr into stdout for complete filtering
        # We use shell=True to allow Windows built-in commands (like 'echo' or 'dir')
        result = subprocess.run(command, capture_output=True, text=True, check=False, shell=True)
        raw_output = result.stdout + (result.stderr if result.stderr else "")
        
        # Pass the massive output bloat into the DeNoiser
        filtered_output = engine.filter_output(raw_output)
        
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
