from pathlib import Path

from tools.environment_detector_tool import detect_environment


def environment_agent(state):

    project_id = state["project_id"]

    project_path = (
        Path(__file__).resolve().parents[2]
        / "projects"
        / project_id
    )

    environment = detect_environment(
        project_path
    )

    print(f"ENVIRONMENT_DETECTED: {environment.get('language', 'unknown')}")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "environment": environment,
        "status": "ENVIRONMENT_DETECTED",
    }