from pathlib import Path

from schemas.test_schema import TestResult
from tools.code_tools import run_tests
from rag import store_test_results


def tester_agent(state):
    """
    Execute the project's tests using the detected environment.

    The Tester Agent is responsible only for running tests and
    reporting the result. It does not attempt to fix code.

    Possible statuses:
        TESTS_PASSED
        TESTS_FAILED
        TESTS_ERROR
    """

    project_id = state["project_id"]
    environment = state.get("environment", {})

    project_path = (
        Path(__file__).resolve().parents[2]
        / "projects"
        / project_id
    )

    print("TESTING")

    # --------------------------------------------------
    # VALIDATE ENVIRONMENT
    # --------------------------------------------------

    if not environment:
        error_message = (
            "No environment configuration available "
            "for test execution."
        )

        print(f"TESTS_ERROR: {error_message}")

        test_result = TestResult(
            status="ERROR",
            exit_code=-1,
            output="",
            errors=[error_message],
        )

        test_result_dict = test_result.model_dump()

        try:
            store_test_results(
                project_id,
                test_result_dict
            )
        except Exception as e:
            print(
                f"Failed to store test results: {e}"
            )

        return {
            "test_result": test_result_dict,
            "status": "TESTS_ERROR",
            "errors": [error_message],
        }

    # --------------------------------------------------
    # RUN TESTS
    # --------------------------------------------------

    try:
        result = run_tests(
            project_path,
            environment
        )

    except Exception as e:

        error_message = (
            f"Unexpected test execution error: {str(e)}"
        )

        print(
            f"TESTS_ERROR: {error_message}"
        )

        test_result = TestResult(
            status="ERROR",
            exit_code=-1,
            output="",
            errors=[error_message],
        )

        test_result_dict = test_result.model_dump()

        try:
            store_test_results(
                project_id,
                test_result_dict
            )
        except Exception as storage_error:
            print(
                f"Failed to store test results: "
                f"{storage_error}"
            )

        return {
            "test_result": test_result_dict,
            "status": "TESTS_ERROR",
            "errors": [error_message],
        }

    # --------------------------------------------------
    # EXTRACT RESULT
    # --------------------------------------------------

    exit_code = result.get(
        "exit_code",
        -1
    )

    output = result.get(
        "output",
        ""
    )

    error_output = result.get(
        "errors",
        ""
    )

    # --------------------------------------------------
    # TESTS PASSED
    # --------------------------------------------------

    if exit_code == 0:

        test_status = "PASSED"
        graph_status = "TESTS_PASSED"
        errors = []

        print("TESTS_PASSED")

    # --------------------------------------------------
    # TEST INFRASTRUCTURE ERROR
    # --------------------------------------------------

    elif exit_code == -1:

        test_status = "ERROR"
        graph_status = "TESTS_ERROR"

        error_message = (
            error_output
            or "Test execution failed before "
               "tests could complete."
        )

        errors = [error_message]

        print(
            f"TESTS_ERROR: {error_message}"
        )

    # --------------------------------------------------
    # ACTUAL TEST FAILURE
    # --------------------------------------------------

    else:

        test_status = "FAILED"
        graph_status = "TESTS_FAILED"

        error_message = (
            error_output
            or "One or more tests failed."
        )

        errors = [error_message]

        print(
            f"TESTS_FAILED: exit code {exit_code}"
        )

    # --------------------------------------------------
    # CREATE TEST RESULT
    # --------------------------------------------------

    test_result = TestResult(
        status=test_status,
        exit_code=exit_code,
        output=output,
        errors=errors,
    )

    test_result_dict = test_result.model_dump()

    # --------------------------------------------------
    # STORE TEST RESULT IN RAG
    # --------------------------------------------------

    try:

        store_test_results(
            project_id,
            test_result_dict
        )

        print(
            "Test results stored in ChromaDB memory"
        )

    except Exception as e:

        # RAG failure must not affect test result
        print(
            f"Failed to store test results: {e}"
        )

    # --------------------------------------------------
    # RETURN STATE
    # --------------------------------------------------

    # Only keep errors from the CURRENT test execution.
    # This prevents errors from previous iterations
    # accumulating indefinitely.

    return {
        "test_result": test_result_dict,
        "status": graph_status,
        "errors": errors,
    }

