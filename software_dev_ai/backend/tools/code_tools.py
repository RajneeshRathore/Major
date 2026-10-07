import subprocess
import sys
from pathlib import Path


# ============================================================
# GENERIC COMMAND RUNNER
# ============================================================

def run_command(
    command: list[str],
    cwd: Path,
    timeout: int = 120
):
    """
    Execute a command inside the given working directory.

    Returns:
        {
            "exit_code": int,
            "output": str,
            "errors": str
        }
    """

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
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
            "errors": (
                f"Command timed out after {timeout} seconds: "
                f"{' '.join(command)}"
            )
        }

    except FileNotFoundError as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": (
                f"Command not found: {command[0]}. "
                f"Make sure it is installed and available in PATH. "
                f"Error: {e}"
            )
        }

    except Exception as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": str(e)
        }


# ============================================================
# FIND PYTHON TEST FILES
# ============================================================

def has_python_tests(project_path: Path) -> bool:
    """
    Check recursively whether the project contains Python
    test files.

    Supports common pytest naming conventions:

        test_*.py
        *_test.py
    """

    test_files = (
        list(project_path.rglob("test_*.py"))
        + list(project_path.rglob("*_test.py"))
    )

    # Ignore files inside virtual environments
    test_files = [
        file
        for file in test_files
        if ".venv" not in file.parts
        and "node_modules" not in file.parts
    ]

    return bool(test_files)


# ============================================================
# PYTHON TESTS
# ============================================================

def run_python_tests(project_path: Path):
    """
    Run Python tests using the project's virtual environment
    when available.

    Falls back to the current Python interpreter when no
    project virtual environment exists.
    """

    # --------------------------------------------------------
    # Locate project virtual environment
    # --------------------------------------------------------

    if sys.platform == "win32":

        venv_python = (
            project_path
            / ".venv"
            / "Scripts"
            / "python.exe"
        )

    else:

        venv_python = (
            project_path
            / ".venv"
            / "bin"
            / "python"
        )

    # --------------------------------------------------------
    # Choose Python executable
    # --------------------------------------------------------

    if venv_python.exists():

        python_executable = str(
            venv_python
        )

    else:

        python_executable = sys.executable

    # --------------------------------------------------------
    # Check whether tests exist
    # --------------------------------------------------------

    if not has_python_tests(project_path):

        return {
            "exit_code": 0,
            "output": (
                "No Python test files found. "
                "Skipping tests."
            ),
            "errors": ""
        }

    # --------------------------------------------------------
    # Run pytest
    # --------------------------------------------------------

    command = [
        python_executable,
        "-m",
        "pytest",
        "-v"
    ]

    print(
        f"PYTHON TESTS: Running {' '.join(command)}"
    )

    return run_command(
        command,
        project_path,
        timeout=120
    )


# ============================================================
# GENERAL TEST RUNNER
# ============================================================

def run_tests(
    project_path: Path,
    environment: dict = None
):
    """
    Run project tests using the detected environment.

    Supported environments:

        Python
        JavaScript / TypeScript
        Java / Maven
        Java / Gradle
        Go
        Rust
        C / C++

    Returns:

        {
            "exit_code": int,
            "output": str,
            "errors": str
        }
    """

    if environment is None:
        environment = {}

    language = environment.get(
        "language",
        "unknown"
    ).lower()

    print(
        f"TEST RUNNER: language={language}"
    )

    # ========================================================
    # PYTHON
    # ========================================================

    if "python" in language:

        return run_python_tests(
            project_path
        )

    # ========================================================
    # JAVASCRIPT / TYPESCRIPT
    # ========================================================

    if (
        "javascript" in language
        or "typescript" in language
        or "node" in language
    ):

        test_command = environment.get(
            "test_command",
            []
        )

        if not test_command:

            return {
                "exit_code": 0,
                "output": (
                    "No Node.js test command configured. "
                    "Skipping tests."
                ),
                "errors": ""
            }

        return run_command(
            test_command,
            project_path,
            timeout=120
        )

    # ========================================================
    # JAVA
    # ========================================================

    if (
        "java" in language
        and "javascript" not in language
    ):

        # Maven
        if (
            (project_path / "pom.xml").exists()
        ):

            return run_command(
                ["mvn", "test"],
                project_path,
                timeout=180
            )

        # Gradle wrapper
        if (
            (project_path / "gradlew.bat").exists()
            and sys.platform == "win32"
        ):

            return run_command(
                ["gradlew.bat", "test"],
                project_path,
                timeout=180
            )

        if (
            (project_path / "gradlew").exists()
            and sys.platform != "win32"
        ):

            return run_command(
                ["./gradlew", "test"],
                project_path,
                timeout=180
            )

        # System Gradle
        if (
            (project_path / "build.gradle").exists()
            or
            (project_path / "build.gradle.kts").exists()
        ):

            return run_command(
                ["gradle", "test"],
                project_path,
                timeout=180
            )

        return {
            "exit_code": 0,
            "output": (
                "No Java test configuration found. "
                "Skipping tests."
            ),
            "errors": ""
        }

    # ========================================================
    # GO
    # ========================================================

    if "go" in language:

        if not (project_path / "go.mod").exists():

            return {
                "exit_code": 0,
                "output": (
                    "go.mod not found. "
                    "Skipping Go tests."
                ),
                "errors": ""
            }

        return run_command(
            ["go", "test", "./..."],
            project_path,
            timeout=180
        )

    # ========================================================
    # RUST
    # ========================================================

    if "rust" in language:

        if not (project_path / "Cargo.toml").exists():

            return {
                "exit_code": 0,
                "output": (
                    "Cargo.toml not found. "
                    "Skipping Rust tests."
                ),
                "errors": ""
            }

        return run_command(
            ["cargo", "test"],
            project_path,
            timeout=180
        )

    # ========================================================
    # CUSTOM TEST COMMAND
    # ========================================================

    test_command = environment.get(
        "test_command",
        []
    )

    if test_command:

        return run_command(
            test_command,
            project_path,
            timeout=120
        )

    # ========================================================
    # UNKNOWN LANGUAGE
    # ========================================================

    return {
        "exit_code": 0,
        "output": (
            f"No test runner configured for "
            f"language '{language}'. "
            f"Skipping tests."
        ),
        "errors": ""
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def run_python_tests_legacy(project_path: Path):
    """
    Backward-compatible helper.

    Prefer run_python_tests() or run_tests().
    """

    return run_python_tests(
        project_path
    )

