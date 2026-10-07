from llm.model import llm
from agents.code_schema import CodeGenerationResult
from rag import retrieve_context


coder_llm = llm.with_structured_output(
    CodeGenerationResult
)


def coder_agent(state):

    print("CODING")

    requirement = state["user_requirement"]
    plan = state["plan"]
    project_id = state["project_id"]
    iteration = state.get("iteration", 0)
    errors = state.get("errors", [])
    test_result = state.get("test_result", {})

    print(f"plan (Iteration {iteration})")

    # Retrieve context from RAG memory
    context_str = ""
    try:
        # Search for context relevant to the requirement
        context_items = retrieve_context(project_id, requirement, n_results=5)
        if context_items:
            context_str = "Relevant context from past files/history:\n"
            for item in context_items:
                doc_type = item["metadata"].get("type", "unknown")
                filepath = item["metadata"].get("file_path", "")

                if doc_type == "source_file":
                    context_str += f"--- {filepath} ---\n{item['document'][:500]}...\n"
                elif doc_type == "test_result":
                    context_str += f"--- Past Test Result ---\n{item['document']}\n"
    except Exception as e:
        print(f"Failed to retrieve context: {e}")

    # Format feedback if this is a retry
    feedback_str = ""
    if iteration > 0:
        feedback_str = f"""
This is iteration {iteration}. Your previous attempt had issues.
Errors encountered:
{errors}

Test results from previous run:
{test_result}

Please fix the errors and ensure all tests pass.
"""

    prompt = f"""
You are the Coding Agent in an AI software development platform.

Your responsibility is to implement the development plan
provided by the Planner Agent.

Developer requirement:
{requirement}

Development plan:
{plan}

{feedback_str}

{context_str}

Instructions:

1. Implement the required functionality from the development plan.
2. Generate complete source files.
3. Each file must have a clear relative path.
4. Each file must contain complete code — NOT wrapped in markdown code fences.
5. Do not return explanations outside the structured output.
6. Do not leave TODO placeholders.
7. Follow good software engineering practices.
8. Generate only files necessary for the current implementation or fix.
9. Include a requirements.txt or package.json with all dependencies.
10. Write simple, self-contained test files that can run independently.
11. CRITICAL: Always use modern, up-to-date dependencies. For React projects, you MUST use Vite and React 18+. DO NOT use create-react-app (`react-scripts`) as it is deprecated and fails on modern Node.js environments.
"""

    
    from utils.streaming import CoderStreamHandler
    handler = CoderStreamHandler(project_id)
    result = coder_llm.invoke(prompt, config={"callbacks": [handler]})

    print("FINALIZING_CODE")

    def clean_content(text: str) -> str:
        import re
        text = text.strip()
        match = re.search(r"```(?:\w+\n)?(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text

    files = {
        file.path: clean_content(file.content)
        for file in result.files
    }

    print("CODE_GENERATED")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "files": files,
        "status": "CODE_GENERATED",
    }