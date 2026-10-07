import subprocess
import sys
from pathlib import Path


def run_command(
    command: list[str],
    cwd: Path,
    timeout: int = 120
):

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
                f"Command timed out after {timeout} seconds."
            )
        }

    except FileNotFoundError as e:

        return {
            "exit_code": -1,
            "output": "",
            "errors": f"Command not found: {command}. Error: {e}"
        }

    except Exception as e:

        return {
            "exit_code": -1,
            "output": "",
            "errors": str(e)
        }


def setup_python_environment(project_path: Path):

    venv_path = project_path / ".venv"

    if not venv_path.exists():

        result = run_command(
            [
                sys.executable,
                "-m",
                "venv",
                ".venv"
            ],
            project_path
        )

        if result["exit_code"] != 0:

            return result

    if sys.platform == "win32":

        python_executable = (
            venv_path
            / "Scripts"
            / "python.exe"
        )

    else:

        python_executable = (
            venv_path
            / "bin"
            / "python"
        )

    # Install pytest in the venv so tests can actually run
    run_command(
        [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "pytest",
        ],
        project_path,
        timeout=120
    )

    requirements = project_path / "requirements.txt"

    if requirements.exists():

        result = run_command(
            [
                str(python_executable),
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt"
            ],
            project_path,
            timeout=300
        )

        if result["exit_code"] != 0:

            return result

    return {
        "exit_code": 0,
        "output": (
            f"Python environment ready: "
            f"{venv_path}"
        ),
        "errors": ""
    }


def setup_node_environment(project_path: Path):

    package_json = project_path / "package.json"

    if not package_json.exists():

        return {
            "exit_code": -1,
            "output": "",
            "errors": "package.json not found."
        }

    result = run_command(
        [
            "npm",
            "install"
        ],
        project_path,
        timeout=300
    )

    return result


def setup_maven_environment(project_path: Path):

    pom_file = project_path / "pom.xml"

    if not pom_file.exists():

        return {
            "exit_code": -1,
            "output": "",
            "errors": "pom.xml not found."
        }

    result = run_command(
        [
            "mvn",
            "dependency:resolve"
        ],
        project_path,
        timeout=300
    )

    return result


def setup_environment(
    project_path: Path,
    environment: dict
):

    language = environment.get("language", "unknown").lower()

    # Handle language string variations (e.g., "javascript/typescript" -> "javascript")
    if "python" in language:
        return setup_python_environment(project_path)

    if "javascript" in language or "typescript" in language or "node" in language:
        return setup_node_environment(project_path)

    if "java" in language and "javascript" not in language:
        return setup_maven_environment(project_path)

    # For languages that don't need environment setup (Go, Rust, C, etc.)
    # try running the install_command if provided
    install_cmd = environment.get("install_command", [])
    if install_cmd:
        result = run_command(install_cmd, project_path, timeout=300)
        return result

    # No setup needed
    return {
        "exit_code": 0,
        "output": f"No environment setup needed for language: {language}",
        "errors": ""
    }