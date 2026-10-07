from llm.model import llm


def reviewer_agent(state):
    """Review test results and decide whether to approve or request a retry."""

    print("REVIEWING")

    test_result = state.get("test_result", {})
    files = state.get("files", {})
    plan = state.get("plan", {})
    errors = state.get("errors", [])
    iteration = state.get("iteration", 0)

    # Build a summary of generated files for the reviewer
    file_list = "\n".join(
        f"  - {path}" for path in files.keys()
    ) if files else "  (no files generated)"

    prompt = f"""
You are the Reviewer Agent of an AI software development platform.

Your job is to review the development output and decide whether
the project is ready for delivery or needs more work.

Development Plan:
{plan}

Generated Files:
{file_list}

Test Results:
{test_result}

Errors Encountered:
{errors}

Current Iteration: {iteration}

Instructions:
1. If tests passed and the code looks complete, respond with exactly: APPROVED
2. If there are failures, errors, or missing functionality, respond with exactly: NEEDS_REVISION
3. Do NOT write any explanation — respond with only one of the two words above.
"""

    response = llm.invoke(prompt)

    # Extract the text content from the response
    review_text = response.content.strip().upper()

    if "APPROVED" in review_text:
        review_result = "APPROVED"
        status = "COMPLETED"
        next_iter = iteration
        print("REVIEW: APPROVED")
    else:
        review_result = "NEEDS_REVISION"
        next_iter = iteration + 1

        if next_iter >= 3:
            status = "FAILED"
            print(f"REVIEW: FAILED (max iterations reached)")
        else:
            status = "NEEDS_REVISION"
            print(f"REVIEW: NEEDS_REVISION (iteration {next_iter})")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "review_result": review_result,
        "status": status,
        "iteration": next_iter,
    }
