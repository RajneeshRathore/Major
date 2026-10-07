import subprocess
import sys
from pathlib import Path

# ============================================================
# COMMAND EXECUTION
# ============================================================

def run_command(command: list[str], cwd: Path, timeout: int = 120):
    """
    Execute a command inside the given project directory.

    Returns a consistent result dictionary used by the
    runtime and testing agents.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        return {
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "output": "",
            "errors": f"Command timed out after {timeout} seconds.",
        }

    except FileNotFoundError as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": f"Command not found: {command}. Error: {e}",
        }

    except Exception as e:
        return {
            "exit_code": -1,
            "output": "",
            "errors": str(e),
        }

# ============================================================
# PYTHON STANDARD LIBRARY
# ============================================================

PYTHON_STDLIB_MODULES = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii", 
    "bisect", "builtins", "calendar", "cmath", "cmd", "code", "codecs", 
    "collections", "colorsys", "concurrent", "configparser", "contextlib", 
    "copy", "csv", "dataclasses", "datetime", "decimal", "difflib", "email", 
    "enum", "errno", "faulthandler", "filecmp", "fileinput", "fnmatch", 
    "fractions", "functools", "gc", "getopt", "getpass", "gettext", "glob", 
    "gzip", "hashlib", "heapq", "hmac", "html", "http", "imaplib", "importlib", 
    "inspect", "io", "ipaddress", "itertools", "json", "keyword", "logging", 
    "lzma", "math", "mimetypes", "multiprocessing", "numbers", "operator", 
    "os", "pathlib", "pickle", "platform", "plistlib", "pprint", "profile", 
    "pstats", "queue", "random", "re", "secrets", "selectors", "shlex", 
    "shutil", "signal", "shelve", "site", "smtplib", "socket", "sqlite3", 
    "ssl", "statistics", "string", "stringprep", "struct", "subprocess", 
    "sys", "tempfile", "textwrap", "threading", "time", "timeit", "traceback", 
    "types", "typing", "unicodedata", "unittest", "urllib", "uuid", "warnings", 
    "wave", "weakref", "xml", "zipfile", "zoneinfo",
}

# ============================================================
# PYTHON REQUIREMENTS VALIDATION
# ============================================================

def validate_python_requirements(project_path: Path):
    """
    Validate requirements.txt before pip installation.

    Python standard-library modules such as 'json', 'os',
    'sys', 'pathlib', etc. must never be installed through pip.

    Invalid standard-library entries are removed automatically.

    Returns:
        {
            "removed": [...],
            "remaining": [...]
        }
    """
    requirements_file = project_path / "requirements.txt"

    if not requirements_file.exists():
        return {
            "removed": [],
            "remaining": [],
        }

    try:
        lines = requirements_file.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"WARNING: Could not read requirements.txt: {e}")
        return {
            "removed": [],
            "remaining": [],
        }

    valid_lines = []
    removed = []

    for line in lines:
        stripped = line.strip()

        # Preserve empty lines.
        if not stripped:
            valid_lines.append(line)
            continue

        # Preserve comments.
        if stripped.startswith("#"):
            valid_lines.append(line)
            continue

        # Preserve pip options.
        if stripped.startswith("-"):
            valid_lines.append(line)
            continue

        # Remove inline comments for dependency inspection.
        dependency = stripped.split("#", 1)[0].strip()

        # ----------------------------------------------------
        # Extract package name.
        #
        # Examples:
        # requests
        # requests==2.32.0
        # requests>=2.0
        # requests[security]
        # ----------------------------------------------------
        package_name = dependency

        for separator in ("==", ">=", "<=", "~=", "!=", ">", "<", "[", ";"):
            if separator in package_name:
                package_name = package_name.split(separator, 1)[0]

        package_name = package_name.strip().lower()

        # ----------------------------------------------------
        # Remove Python standard-library modules.
        # ----------------------------------------------------
        if package_name in PYTHON_STDLIB_MODULES:
            print(
                f"Removing Python standard-library dependency "
                f"from requirements.txt: {package_name}"
            )
            removed.append(package_name)
            continue

        valid_lines.append(line)

    # --------------------------------------------------------
    # Rewrite requirements.txt if anything was removed.
    # --------------------------------------------------------
    if removed:
        requirements_file.write_text(
            "\n".join(valid_lines).rstrip() + "\n",
            encoding="utf-8",
        )
        print(f"Removed invalid Python dependencies: {removed}")

    return {
        "removed": removed,
        "remaining": [
            line.strip()
            for line in valid_lines
            if line.strip()
            and not line.strip().startswith("#")
            and not line.strip().startswith("-")
        ],
    }

# ============================================================
# PYTHON ENVIRONMENT
# ============================================================

def setup_python_environment(project_path: Path, environment: dict):
    """
    Create a Python virtual environment and install the
    dependencies specified by the detected environment.
    """
    venv_path = project_path / ".venv"

    # --------------------------------------------------------
    # Create virtual environment
    # --------------------------------------------------------
    if not venv_path.exists():
        print("Creating Python virtual environment...")

        result = run_command(
            [sys.executable, "-m", "venv", ".venv"],
            project_path,
            timeout=120,
        )

        if result["exit_code"] != 0:
            return result

    # --------------------------------------------------------
    # Locate virtual-environment Python
    # --------------------------------------------------------
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        python_executable = venv_path / "bin" / "python"

    if not python_executable.exists():
        return {
            "exit_code": -1,
            "output": "",
            "errors": f"Python executable was not found at {python_executable}",
        }

    # --------------------------------------------------------
    # Upgrade pip
    # --------------------------------------------------------
    print("Upgrading pip...")

    result = run_command(
        [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
        project_path,
        timeout=120,
    )

    if result["exit_code"] != 0:
        return result

    # --------------------------------------------------------
    # Validate requirements.txt
    # --------------------------------------------------------
    validation_result = validate_python_requirements(project_path)
    removed_dependencies = validation_result.get("removed", [])

    if removed_dependencies:
        print(
            "Invalid standard-library dependencies "
            "were removed before pip installation."
        )

    # --------------------------------------------------------
    # Install dependencies
    # --------------------------------------------------------
    install_command = environment.get("install_command", [])

    if install_command:
        # Replace generic Python executable with virtual-environment Python.
        if install_command[0] in ("python", "python3"):
            install_command = [str(python_executable)] + install_command[1:]

        print(f"Installing Python dependencies: {install_command}")

        result = run_command(
            install_command,
            project_path,
            timeout=300,
        )

        if result["exit_code"] != 0:
            return result

    return {
        "exit_code": 0,
        "output": f"Python environment ready: {venv_path}",
        "errors": "",
        "environment_path": str(venv_path.resolve()),
        "removed_dependencies": removed_dependencies,
    }

# ============================================================
# NODE.JS ENVIRONMENT
# ============================================================

def setup_node_environment(project_path: Path, environment: dict):
    """
    Install Node.js dependencies using the package manager
    detected by environment_detector.py.
    """
    package_json = project_path / "package.json"

    if not package_json.exists():
        return {
            "exit_code": -1,
            "output": "",
            "errors": "package.json not found.",
        }

    install_command = environment.get("install_command", [])

    if not install_command:
        package_manager = environment.get("package_manager", "npm")
        install_command = [package_manager, "install"]

    print(f"Installing Node dependencies: {install_command}")

    result = run_command(
        install_command,
        project_path,
        timeout=300,
    )

    if result["exit_code"] != 0:
        return result

    return {
        "exit_code": 0,
        "output": result["output"],
        "errors": result["errors"],
        "environment_path": str((project_path / "node_modules").resolve()),
    }

# ============================================================
# MAVEN ENVIRONMENT
# ============================================================

def setup_maven_environment(project_path: Path, environment: dict):
    """
    Resolve Maven dependencies using the command selected by
    environment_detector.py.

    Supports Maven and Maven Wrapper.
    """
    pom_file = project_path / "pom.xml"

    if not pom_file.exists():
        return {
            "exit_code": -1,
            "output": "",
            "errors": "pom.xml not found.",
        }

    install_command = environment.get("install_command", [])

    if not install_command:
        install_command = ["mvn", "dependency:resolve"]

    print(f"Resolving Maven dependencies: {install_command}")

    result = run_command(
        install_command,
        project_path,
        timeout=300,
    )

    if result["exit_code"] != 0:
        return result

    return {
        "exit_code": 0,
        "output": result["output"],
        "errors": result["errors"],
        "environment_path": str(project_path.resolve()),
    }

# ============================================================
# GENERIC ENVIRONMENT
# ============================================================

def setup_generic_environment(project_path: Path, environment: dict):
    """
    Execute the installation command supplied by the
    environment detector.

    Used for Go, Rust and other supported environments.
    """
    install_command = environment.get("install_command", [])

    if not install_command:
        return {
            "exit_code": 0,
            "output": "No environment setup required.",
            "errors": "",
            "environment_path": str(project_path.resolve()),
        }

    print(f"Running environment setup: {install_command}")

    result = run_command(
        install_command,
        project_path,
        timeout=300,
    )

    if result["exit_code"] != 0:
        return result

    return {
        "exit_code": 0,
        "output": result["output"],
        "errors": result["errors"],
        "environment_path": str(project_path.resolve()),
    }

# ============================================================
# MAIN ENVIRONMENT SETUP
# ============================================================

def setup_environment(project_path: Path, environment: dict):
    """
    Set up the project according to the environment detected
    by environment_detector.py.

    Architecture:

        environment_detector.py
                ↓
        environment dictionary
                ↓
        runtime_manager.py
                ↓
        actual commands
    """
    if not project_path.exists():
        return {
            "exit_code": -1,
            "output": "",
            "errors": f"Project directory does not exist: {project_path}",
        }

    if not environment:
        return {
            "exit_code": -1,
            "output": "",
            "errors": "No environment configuration was provided.",
        }

    language = environment.get("language", "unknown").lower()

    print(f"Setting up environment for: {language}")

    # --------------------------------------------------------
    # Python
    # --------------------------------------------------------
    if "python" in language:
        return setup_python_environment(project_path, environment)

    # --------------------------------------------------------
    # JavaScript / TypeScript / Node
    # --------------------------------------------------------
    if "javascript" in language or "typescript" in language or language == "node":
        return setup_node_environment(project_path, environment)

    # --------------------------------------------------------
    # Java / Maven / Gradle
    # --------------------------------------------------------
    if "java" in language:
        build_tool = environment.get("build_tool", "").lower()

        if build_tool == "maven":
            return setup_maven_environment(project_path, environment)

        return setup_generic_environment(project_path, environment)

    # --------------------------------------------------------
    # Everything else
    # --------------------------------------------------------
    return setup_generic_environment(project_path, environment)