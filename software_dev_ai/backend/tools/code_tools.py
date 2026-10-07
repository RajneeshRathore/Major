import subprocess
import sys
from pathlib import Path


def run_tests(project_path: Path, environment: dict = None):
    """
    Run tests using the test command from the detected environment.
    Falls back to pytest for Python projects if no command is specified.
    """

    test_command = None

    if environment:
        test_command = environment.get("test_command", [])
        language = environment.get("language", "unknown")
    else:
        language = "unknown"

    # If no test command from environment, try to detect
    if not test_command:
        # Check if there are any test files at all
        test_files = list(project_path.glob("*test*")) + list(project_path.glob("*_test*"))
        if not test_files:
            # No tests to run — report success
            return {
                "exit_code": 0,
                "output": "No test files found. Skipping tests.",
                "errors": ""
            }

        # Default to pytest for Python
        if language in ("python",):
            test_command = [sys.executable, "-m", "pytest", "-v"]
        else:
            return {
                "exit_code": 0,
                "output": f"No test command configured for language '{language}'. Skipping tests.",
                "errors": ""
            }

    # For Python projects, use the venv's python if available
    if language in ("python",):
        venv_python = project_path / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
        if venv_python.exists():
            # Replace 'python' with the venv python
            test_command = [str(venv_python)] + test_command[1:] if test_command[0] in ("python", "python3") else test_command

    try:
        result = subprocess.run(
            test_command,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "output": "",
            "errors": "Test execution timed out after 120 seconds."
        }

    except FileNotFoundError as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": f"Test command not found: {test_command}. Error: {e}"
        }

    except Exception as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": str(e)
        }


# Keep backward compatibility
def run_python_tests(project_path: Path):
    """Legacy function — prefer run_tests() with environment dict."""
    return run_tests(project_path, {"language": "python", "test_command": [sys.executable, "-m", "pytest", "-v"]})