from llm.model import llm

MAX_ITERATIONS = 3

def reviewer_agent(state):
    """
    Review the complete development result.

    The Reviewer combines deterministic execution results
    with an LLM-based quality review.

    Deterministic failures always override an LLM approval.
    """
    print("REVIEWING")

    # --------------------------------------------------
    # READ STATE
    # --------------------------------------------------
    test_result = state.get("test_result", {})
    files = state.get("files", {})
    plan = state.get("plan", {})
    errors = state.get("errors", [])
    iteration = state.get("iteration", 0)
    status = state.get("status", "")
    runtime_result = state.get("runtime_result", {})

    # --------------------------------------------------
    # BUILD FILE LIST
    # --------------------------------------------------
    file_list = "\n".join(
        f"  - {path}"
        for path in files.keys()
    ) if files else "  (no files generated)"

    # --------------------------------------------------
    # EXTRACT TEST STATUS
    # --------------------------------------------------
    test_status = test_result.get("status", "UNKNOWN")
    test_exit_code = test_result.get("exit_code", -1)

    # --------------------------------------------------
    # DETERMINISTIC FAILURE CHECKS
    # --------------------------------------------------
    blocking_statuses = {
        "FILE_WRITING_FAILED",
        "RUNTIME_FAILED",
        "TESTS_FAILED",
        "TESTS_ERROR",
        "ENVIRONMENT_SETUP_FAILED",
    }

    if status in blocking_statuses:
        print(f"REVIEW: BLOCKED by status {status}")

        if iteration >= MAX_ITERATIONS:
            print("REVIEW: FAILED — maximum iterations reached")
            return {
                "review_result": "NEEDS_REVISION",
                "status": "FAILED",
                "iteration": iteration,
            }

        next_iteration = iteration + 1
        print(f"REVIEW: NEEDS_REVISION (iteration {next_iteration})")

        return {
            "review_result": "NEEDS_REVISION",
            "status": "NEEDS_REVISION",
            "iteration": next_iteration,
        }

    # --------------------------------------------------
    # ADDITIONAL TEST SAFETY CHECK
    # --------------------------------------------------
    if test_status != "PASSED" or test_exit_code != 0:
        print("REVIEW: Tests did not pass — revision required")

        if iteration >= MAX_ITERATIONS:
            print("REVIEW: FAILED — maximum iterations reached")
            return {
                "review_result": "NEEDS_REVISION",
                "status": "FAILED",
                "iteration": iteration,
            }

        next_iteration = iteration + 1

        return {
            "review_result": "NEEDS_REVISION",
            "status": "NEEDS_REVISION",
            "iteration": next_iteration,
        }

    # --------------------------------------------------
    # LLM QUALITY REVIEW
    # --------------------------------------------------
    prompt = f"""
You are the Reviewer Agent of an AI software development platform.

Your job is to determine whether the generated project is complete
and ready to be delivered to the developer.

The project has already passed its automated tests.

Development Plan:
{plan}

Generated Files:
{file_list}

Runtime Result:
{runtime_result}

Test Results:
{test_result}

Errors Encountered:
{errors}

Current Iteration:
{iteration}

Review the project against the development plan.

Check:
1. Does the implementation satisfy the requested functionality?
2. Are the major planned components present?
3. Are the generated files logically complete?
4. Are there obvious missing dependencies or configuration?
5. Are there obvious placeholders such as TODO or incomplete code?
6. Does the implementation appear consistent with the requested architecture?

IMPORTANT:
The automated tests have already passed.

If the project is complete and ready for delivery, respond with exactly:
APPROVED

Otherwise respond with exactly:
NEEDS_REVISION

Do NOT provide any explanation.
Return only one of those two values.
"""

    # --------------------------------------------------
    # INVOKE REVIEWER LLM
    # --------------------------------------------------
    try:
        response = llm.invoke(prompt)
        review_text = response.content.strip().upper()

    except Exception as e:
        print(f"REVIEWER LLM ERROR: {e}")

        # A reviewer failure should not accidentally approve
        # the project.
        if iteration >= MAX_ITERATIONS:
            return {
                "review_result": "NEEDS_REVISION",
                "status": "FAILED",
                "iteration": iteration,
            }

        next_iteration = iteration + 1
        return {
            "review_result": "NEEDS_REVISION",
            "status": "NEEDS_REVISION",
            "iteration": next_iteration,
        }

    # --------------------------------------------------
    # PARSE REVIEW
    # --------------------------------------------------
    if review_text == "APPROVED":
        print("REVIEW: APPROVED")
        return {
            "review_result": "APPROVED",
            "status": "COMPLETED",
            "iteration": iteration,
        }

    # Anything other than an exact APPROVED response
    # is treated as a revision request.
    print(f"REVIEW: NEEDS_REVISION (LLM response: {review_text})")

    if iteration >= MAX_ITERATIONS:
        print("REVIEW: FAILED — maximum iterations reached")
        return {
            "review_result": "NEEDS_REVISION",
            "status": "FAILED",
            "iteration": iteration,
        }

    next_iteration = iteration + 1
    return {
        "review_result": "NEEDS_REVISION",
        "status": "NEEDS_REVISION",
        "iteration": next_iteration,
    }