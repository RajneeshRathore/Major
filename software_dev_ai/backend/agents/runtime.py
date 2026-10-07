from pathlib import Path
from tools.runtime_manager import setup_environment

def runtime_agent(state):
    """
    Prepare the project's runtime environment.

    The environment configuration is produced by the
    Environment Agent and contains information such as:

    - language
    - package manager
    - environment type
    - install command
    - build command
    - test command

    If environment setup fails, the graph can send the project
    back to the Coder Agent for another iteration.
    """
    project_id = state["project_id"]

    project_path = (
        Path(__file__).resolve().parents[2]
        / "projects"
        / project_id
    )

    environment = state.get("environment", {})

    print("SETTING_UP_RUNTIME")

    # --------------------------------------------------
    # VALIDATE ENVIRONMENT
    # --------------------------------------------------
    if not environment:
        error_message = (
            "No environment configuration was provided "
            "by the Environment Agent."
        )

        print(f"RUNTIME_FAILED: {error_message}")
        previous_errors = state.get("errors", [])

        return {
            "runtime_result": {
                "exit_code": -1,
                "output": "",
                "errors": error_message,
            },
            "status": "RUNTIME_FAILED",
            "errors": previous_errors + [error_message],
        }

    # --------------------------------------------------
    # SETUP ENVIRONMENT
    # --------------------------------------------------
    try:
        result = setup_environment(
            project_path,
            environment
        )

    except Exception as e:
        error_message = f"Unexpected runtime setup error: {str(e)}"
        print(f"RUNTIME_FAILED: {error_message}")
        previous_errors = state.get("errors", [])

        return {
            "runtime_result": {
                "exit_code": -1,
                "output": "",
                "errors": error_message,
            },
            "status": "RUNTIME_FAILED",
            "errors": previous_errors + [error_message],
        }

    # --------------------------------------------------
    # HANDLE FAILURE
    # --------------------------------------------------
    if result.get("exit_code", -1) != 0:
        error_message = result.get(
            "errors",
            "Unknown environment setup error."
        )

        print(f"RUNTIME_FAILED: {error_message}")
        previous_errors = state.get("errors", [])

        return {
            "runtime_result": result,
            "status": "RUNTIME_FAILED",
            "errors": previous_errors + [error_message],
        }

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------
    print("RUNTIME_READY")

    return {
        "runtime_result": result,
        "status": "RUNTIME_READY",
    }