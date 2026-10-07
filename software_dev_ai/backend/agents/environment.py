from pathlib import Path

from tools.environment_detector_tool import detect_environment


def environment_agent(state):
    """
    Detect the project's programming language, package manager,
    build tool, and commands required to install, build, and test
    the generated project.

    The detected environment is stored in:

        state["environment"]

    Possible statuses:

        ENVIRONMENT_DETECTED
        ENVIRONMENT_FAILED
    """

    project_id = state["project_id"]

    project_path = (
        Path(__file__).resolve().parents[2]
        / "projects"
        / project_id
    )

    print("DETECTING_ENVIRONMENT")

    # ============================================================
    # VALIDATE PROJECT DIRECTORY
    # ============================================================

    if not project_path.exists():

        error_message = (
            f"Project directory does not exist: {project_path}"
        )

        print(
            f"ENVIRONMENT_DETECTION_FAILED: {error_message}"
        )

        previous_errors = state.get("errors", [])

        return {
            "environment": {},
            "status": "ENVIRONMENT_FAILED",
            "errors": previous_errors + [error_message],
        }

    # ============================================================
    # DETECT ENVIRONMENT
    # ============================================================

    try:

        environment = detect_environment(project_path)

    except Exception as e:

        error_message = (
            f"Environment detection failed: {str(e)}"
        )

        print(
            f"ENVIRONMENT_DETECTION_FAILED: {error_message}"
        )

        previous_errors = state.get("errors", [])

        return {
            "environment": {},
            "status": "ENVIRONMENT_FAILED",
            "errors": previous_errors + [error_message],
        }

    # ============================================================
    # VALIDATE DETECTOR RESULT
    # ============================================================

    if not isinstance(environment, dict):

        error_message = (
            "Environment detector returned an invalid "
            "configuration."
        )

        print(
            f"ENVIRONMENT_DETECTION_FAILED: {error_message}"
        )

        previous_errors = state.get("errors", [])

        return {
            "environment": {},
            "status": "ENVIRONMENT_FAILED",
            "errors": previous_errors + [error_message],
        }

    # ============================================================
    # EMPTY ENVIRONMENT
    # ============================================================

    if not environment:

        error_message = (
            "Environment detector returned an empty "
            "configuration."
        )

        print(
            f"ENVIRONMENT_DETECTION_FAILED: {error_message}"
        )

        previous_errors = state.get("errors", [])

        return {
            "environment": {},
            "status": "ENVIRONMENT_FAILED",
            "errors": previous_errors + [error_message],
        }

    # ============================================================
    # UNKNOWN ENVIRONMENT
    # ============================================================

    language = environment.get(
        "language",
        "unknown"
    )

    if language == "unknown":

        error_message = (
            "Unable to detect a supported project environment."
        )

        print(
            f"ENVIRONMENT_DETECTION_FAILED: {error_message}"
        )

        previous_errors = state.get("errors", [])

        return {
            "environment": environment,
            "status": "ENVIRONMENT_FAILED",
            "errors": previous_errors + [error_message],
        }

    # ============================================================
    # SUCCESS
    # ============================================================

    print(
        "ENVIRONMENT_DETECTED: "
        f"language={environment.get('language')}, "
        f"runtime={environment.get('runtime')}, "
        f"package_manager={environment.get('package_manager')}, "
        f"build_tool={environment.get('build_tool')}"
    )

    return {
        "environment": environment,
        "status": "ENVIRONMENT_DETECTED",
    }

