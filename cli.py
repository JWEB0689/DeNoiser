import sys
import subprocess
from filters.engine import engine

VERSION = "v1.4.3"

def print_usage():
    print("Usage: denoiser <command> [args...]")
    print("\nMeta-commands:")
    print("  denoiser version       : Show the current version.")
    print("  denoiser list          : List all loaded TOML filter rules.")
    print("  denoiser test          : Run a built-in diagnostic test to verify filtering.")
    print("  denoiser discover      : Scan local AI agent transcripts to find unfiltered noisy commands.")
    print("  denoiser hook          : Generate and install shell wrappers to automatically intercept AI commands.")
    print("  denoiser hook --dry-run: Preview shell wrappers without installing them.")
    print("\nExample: denoiser git status")

def run_test():
    """Run the built-in diagnostic test covering multiple filter scenarios."""
    print("Running DeNoiser diagnostic test suite...\n")
    
    scenarios = [
        {
            "name": "npm install",
            "command": "npm install fake-package",
            "output": (
                "npm WARN deprecated fake-package@1.0.0: this package is deprecated\n"
                "npm WARN optional SKIPPING OPTIONAL DEPENDENCY: fsevents@2.3.2\n"
                "added 42 packages, and audited 43 packages in 3s\n"
                "found 0 vulnerabilities\n"
                "Successfully installed fake-package!\n"
            ),
        },
        {
            "name": "pip install",
            "command": "pip install requests",
            "output": (
                "Collecting requests\n"
                "  Downloading requests-2.31.0-py3-none-any.whl (62 kB)\n"
                "     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 62.6/62.6 kB 2.1 MB/s eta 0:00:00\n"
                "Collecting urllib3<3,>=1.21.1\n"
                "  Using cached urllib3-2.1.0-py3-none-any.whl\n"
                "Installing collected packages: urllib3, requests\n"
                "Successfully installed requests-2.31.0 urllib3-2.1.0\n"
            ),
        },
        {
            "name": "git push",
            "command": "git push origin main",
            "output": (
                "Enumerating objects: 15, done.\n"
                "Counting objects: 100% (15/15), done.\n"
                "Delta compression using up to 8 threads\n"
                "Compressing objects: 100% (10/10), done.\n"
                "Writing objects: 100% (10/10), 2.51 KiB | 2.51 MiB/s, done.\n"
                "Total 10 (delta 4), reused 0 (delta 0), pack-reused 0\n"
                "remote: Resolving deltas: 100% (4/4), completed with 4 local objects.\n"
                "To github.com:user/repo.git\n"
                "   abc1234..def5678  main -> main\n"
            ),
        },
        {
            "name": "pytest (with failure)",
            "command": "pytest tests/",
            "output": (
                "============================= test session starts ==============================\n"
                "platform linux -- Python 3.11.5, pytest-7.4.3, pluggy-1.3.0\n"
                "collected 5 items\n"
                "\n"
                "tests/test_math.py::test_add PASSED\n"
                "tests/test_math.py::test_subtract PASSED\n"
                "tests/test_math.py::test_multiply PASSED\n"
                "tests/test_math.py::test_divide PASSED\n"
                "tests/test_math.py::test_modulo FAILED\n"
                "\n"
                "=================================== FAILURES ===================================\n"
                "_________________________________ test_modulo __________________________________\n"
                "\n"
                "    def test_modulo():\n"
                ">       assert 10 % 3 == 0\n"
                "E       assert 1 == 0\n"
                "\n"
                "tests/test_math.py:25: AssertionError\n"
                "=========================== short test summary info ============================\n"
                "FAILED tests/test_math.py::test_modulo - assert 1 == 0\n"
                "========================= 1 failed, 4 passed in 0.12s =========================\n"
            ),
        },
        {
            "name": "cargo build",
            "command": "cargo build",
            "output": (
                "   Compiling libc v0.2.150\n"
                "   Compiling cfg-if v1.0.0\n"
                "   Compiling autocfg v1.1.0\n"
                "   Compiling serde v1.0.193\n"
                "   Compiling my-project v0.1.0 (/home/user/my-project)\n"
                "    Finished dev [unoptimized + debuginfo] target(s) in 12.34s\n"
            ),
        },
        {
            "name": "passthrough (echo)",
            "command": "echo hello world",
            "output": "hello world\n",
        },
    ]
    
    total_raw = 0
    total_filtered = 0
    
    for i, scenario in enumerate(scenarios, 1):
        raw = scenario["output"]
        filtered = engine.filter_output(scenario["command"], raw)
        
        raw_lines = len(raw.strip().splitlines())
        filtered_lines = len(filtered.strip().splitlines()) if filtered.strip() else 0
        
        total_raw += len(raw)
        total_filtered += len(filtered)
        
        print(f"━━━ Test {i}/{len(scenarios)}: {scenario['name']} ━━━")
        print(f"  Command:  {scenario['command']}")
        print(f"  Raw:      {raw_lines} lines ({len(raw)} chars)")
        print(f"  Filtered: {filtered_lines} lines ({len(filtered)} chars)")
        print(f"  Result:   {filtered.strip()[:120]}{'...' if len(filtered.strip()) > 120 else ''}")
        print()
    
    if total_raw > 0:
        savings = ((total_raw - total_filtered) / total_raw) * 100
    else:
        savings = 0
    
    print(f"━━━ Summary ━━━")
    print(f"  Total raw chars:      {total_raw}")
    print(f"  Total filtered chars: {total_filtered}")
    print(f"  Token savings:        {savings:.1f}%")
    print(f"\n✓ All {len(scenarios)} diagnostic scenarios completed.")

def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
        
    command = sys.argv[1:]
    
    # --help / -h support
    if command[0] in ("--help", "-h", "help"):
        print_usage()
        sys.exit(0)
    
    # Native Meta-Command Interception
    if command[0] == "version":
        print(f"DeNoiser {VERSION}")
        sys.exit(0)
    elif command[0] == "list":
        print(f"--- Loaded DeNoiser Filters ({len(engine.filters)}) ---")
        for f in engine.filters:
            desc = f.get("description", "")
            desc_str = f" — {desc}" if desc else ""
            print(f"[{f['id']}] -> matches '{f['match_command'].pattern}'{desc_str}")
        sys.exit(0)
    elif command[0] == "test":
        run_test()
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
            dry_run = "--dry-run" in command
            run_hook(dry_run=dry_run)
        except ImportError:
            print("[DeNoiser] Error: hook module not found.")
        sys.exit(0)
    
    # Join command list into a single string for shell execution.
    # shell=True requires a string on Unix; passing a list causes only the
    # first element to be used as the command and the rest to become $0, $1, etc.
    command_str = " ".join(command)
    
    try:
        result = subprocess.run(command_str, capture_output=True, text=True, check=False, shell=True)
        raw_output = result.stdout + (result.stderr if result.stderr else "")
        
        # Pass the raw output into the DeNoiser filter engine
        filtered_output = engine.filter_output(command_str, raw_output)
        
        # Print the filtered result
        print(filtered_output)
        
        # Preserve the original command's exit code
        sys.exit(result.returncode)
        
    except FileNotFoundError:
        print(f"[DeNoiser] Error: Command '{command[0]}' not found.")
        sys.exit(127)
    except Exception as e:
        print(f"[DeNoiser] Interceptor Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
