from pathlib import Path

from agents.test_schema import TestResult
from tools.code_tools import run_tests
from rag import store_test_results


def tester_agent(state):

    project_id = state["project_id"]
    environment = state.get("environment", {})

    project_path = (
        Path(__file__).resolve().parents[2]
        / "projects"
        / project_id
    )

    # Use the test_command from the detected environment instead of hardcoding pytest
    result = run_tests(project_path, environment)

    if result["exit_code"] == 0:
        status = "PASSED"
        errors = []
    else:
        status = "FAILED"
        errors = [result["errors"]]

    test_result = TestResult(
        status=status,
        exit_code=result["exit_code"],
        output=result["output"],
        errors=errors
    )

    test_result_dict = test_result.model_dump()

    try:
        store_test_results(project_id, test_result_dict)
    except Exception as e:
        print(f"Failed to store test results: {e}")

    print(f"TESTS_{status}")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "test_result": test_result_dict,
        "status": f"TESTS_{status}",
    }