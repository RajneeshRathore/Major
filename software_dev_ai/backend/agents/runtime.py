from pathlib import Path

from tools.runtime_manager import setup_environment


def runtime_agent(state):

    project_id = state["project_id"]

    project_path = (
        Path(__file__).resolve().parents[2]
        / "projects"
        / project_id
    )

    environment = state["environment"]

    result = setup_environment(
        project_path,
        environment
    )

    if result["exit_code"] == 0:
        status = "ENVIRONMENT_READY"
        errors = state.get("errors", [])
    else:
        status = "ENVIRONMENT_SETUP_FAILED"
        errors = state.get("errors", []) + [result["errors"]]

    print(f"RUNTIME: {status}")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "runtime_result": result,
        "status": status,
        "errors": errors,
    }