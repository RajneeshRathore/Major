from llm.model import llm
from rag import retrieve_context
from schemas.code_schema import CodeGenerationResult
from utils.streaming import CoderStreamHandler

coder_llm = llm.with_structured_output(CodeGenerationResult)

# ============================================================
# CONTENT CLEANER
# ============================================================

def clean_content(text: str) -> str:
    """
    Remove accidental markdown code fences from generated files.
    """
    if not text:
        return ""

    text = text.strip()

    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()

        # Remove opening ``` or ```python / ```javascript etc.
        if lines:
            lines = lines[1:]

        # Remove closing ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        return "\n".join(lines).strip()

    return text

# ============================================================
# ERROR FORMATTER
# ============================================================

def format_errors(errors) -> str:
    """
    Convert errors from state into a clean string for the LLM.
    """
    if not errors:
        return "No previous errors."

    if isinstance(errors, str):
        return errors

    formatted = []
    for index, error in enumerate(errors, start=1):
        if error:
            formatted.append(f"[Error {index}]\n{str(error)}")

    return "\n\n".join(formatted) or "No previous errors."

# ============================================================
# TEST RESULT FORMATTER
# ============================================================

def format_test_result(test_result: dict) -> str:
    """
    Convert the previous test result into a useful debugging
    report for the coder.
    """
    if not test_result:
        return "No previous test result."

    exit_code = test_result.get("exit_code", "unknown")
    status = test_result.get("status", "unknown")
    output = test_result.get("output", "")
    errors = test_result.get("errors", [])

    if isinstance(errors, list):
        errors_text = "\n".join(str(error) for error in errors if error)
    else:
        errors_text = str(errors)

    return f"""Status:
{status}

Exit code:
{exit_code}

Test output:
{output}

Test errors:
{errors_text}""".strip()

# ============================================================
# RUNTIME RESULT FORMATTER
# ============================================================

def format_runtime_result(runtime_result: dict) -> str:
    """
    Convert the runtime setup result into a clean debugging report.
    """
    if not runtime_result:
        return "No previous runtime result."

    exit_code = runtime_result.get("exit_code", "unknown")
    output = runtime_result.get("output", "")
    errors = runtime_result.get("errors", "")

    return f"""Exit code:
{exit_code}

Runtime output:
{output}

Runtime errors:
{errors}""".strip()

# ============================================================
# RAG CONTEXT
# ============================================================

def get_rag_context(project_id: str, query: str) -> str:
    """
    Retrieve useful project context from ChromaDB.
    """
    try:
        context_items = retrieve_context(project_id, query, n_results=8)

        if not context_items:
            return ""

        context_parts = []

        for item in context_items:
            metadata = item.get("metadata", {})
            document = item.get("document", "")
            doc_type = metadata.get("type", "unknown")
            filepath = metadata.get("file_path", "")

            if doc_type == "source_file":
                # Avoid sending extremely large files.
                document_preview = document[:3000]
                context_parts.append(
                    f"--- Source File: {filepath} ---\n{document_preview}\n"
                )

            elif doc_type == "test_result":
                context_parts.append(
                    f"--- Previous Test Result ---\n{document}\n"
                )

            elif doc_type == "plan":
                context_parts.append(
                    f"--- Development Plan ---\n{document}\n"
                )

        return "\n".join(context_parts).strip()

    except Exception as exc:
        print(f"Failed to retrieve RAG context: {exc}")
        return ""

# ============================================================
# CODER AGENT
# ============================================================

def coder_agent(state):
    """
    Coding Agent.

    First iteration:
        Requirement -> Plan -> Generate implementation
    Retry iteration:
        Previous errors/runtime/test results -> Fix implementation
    """
    print("CODING")

    # --------------------------------------------------------
    # READ STATE
    # --------------------------------------------------------
    requirement = state["user_requirement"]
    plan = state["plan"]
    project_id = state["project_id"]
    iteration = state.get("iteration", 0)
    errors = state.get("errors", [])
    test_result = state.get("test_result", {})
    runtime_result = state.get("runtime_result", {})

    print(f"CODING: iteration {iteration}")

    # --------------------------------------------------------
    # FORMAT PREVIOUS FEEDBACK
    # --------------------------------------------------------
    errors_text = format_errors(errors)
    test_result_text = format_test_result(test_result)
    runtime_result_text = format_runtime_result(runtime_result)

    # --------------------------------------------------------
    # DETERMINE RETRY
    # --------------------------------------------------------
    if iteration > 0:
        retry_instruction = f"""
============================================================
THIS IS A RETRY / DEBUGGING ITERATION
=====================================

The previous implementation failed validation.
You MUST fix the actual root cause.
Do NOT simply regenerate the same code.
Analyze the reported failure carefully.

---
## PREVIOUS ERRORS
{errors_text}

---
## PREVIOUS TEST RESULT
{test_result_text}

---
## PREVIOUS RUNTIME RESULT
{runtime_result_text}

---
## RETRY REQUIREMENTS
1. Identify the root cause of the failure.
2. Modify the implementation to fix the root cause.
3. Do not merely hide or ignore the error.
4. Do not remove tests just because they fail.
5. Keep the implementation consistent across files.
6. Make sure dependencies match the actual imports.
7. If requirements.txt caused the runtime failure, correct requirements.txt.
8. Do not repeat the same broken implementation.
9. Preserve functionality that already works.
10. Only change files that need to be changed.
"""
    else:
        retry_instruction = """
============================================================
THIS IS THE FIRST IMPLEMENTATION ITERATION
==========================================

There is no previous implementation failure to fix.
Implement the project according to the development plan.
"""

    # --------------------------------------------------------
    # BUILD RAG QUERY
    # --------------------------------------------------------
    rag_query = f"""
Developer requirement:
{requirement}

Development plan:
{plan}

Current iteration:
{iteration}

Previous errors:
{errors_text}

Previous test result:
{test_result_text}

Previous runtime result:
{runtime_result_text}
"""

    # --------------------------------------------------------
    # RETRIEVE PROJECT MEMORY
    # --------------------------------------------------------
    context_str = get_rag_context(project_id, rag_query)

    if context_str:
        context_section = f"""
============================================================
PROJECT MEMORY
==============

The following information was retrieved from project memory.
Use it as context when implementing or debugging the project.

{context_str}
"""
    else:
        context_section = """
============================================================
PROJECT MEMORY
==============

No additional project memory was retrieved.
"""

    # ========================================================
    # CODER PROMPT
    # ========================================================
    prompt = f"""
You are the Coding Agent in an AI software development platform.

Your responsibility is to implement the development plan
provided by the Planner Agent.

============================================================
DEVELOPER REQUIREMENT
=====================

{requirement}

============================================================
DEVELOPMENT PLAN
================

{plan}

{retry_instruction}

{context_section}

============================================================
IMPLEMENTATION RULES
====================

1. Implement the required functionality from the development plan.
2. Generate complete source files.
3. Every generated file MUST have a clear relative path.
4. Every generated file MUST contain complete code.
5. Do NOT wrap file contents in markdown code fences.
6. Do NOT write explanations inside file contents.
7. Do NOT leave TODO placeholders.
8. Follow good software engineering practices.
9. Generate only files necessary for the implementation or the current fix.
10. Include all required dependencies.
11. Python projects MUST include requirements.txt when third-party dependencies are required.
12. Node.js projects MUST include package.json.
13. Write simple, self-contained tests that can actually run in the detected environment.
14. Tests must test the actual requested functionality.
15. Never delete a test simply because it fails.
16. Never hide an error.
17. If this is a retry, prioritize fixing the reported failure before adding unrelated functionality.
18. Keep the implementation consistent across all generated files.
19. Do not invent dependencies that are unnecessary.
20. Always use modern, supported dependencies.
21. For React applications, ALWAYS use Vite and React 18+ or newer.
22. NEVER use create-react-app or react-scripts.
23. Ensure imports match the files and dependencies that you generate.
24. Ensure test imports match the actual project structure.
25. Make the project runnable using the detected environment.

============================================================
PYTHON DEPENDENCY RULES
=======================

26. Python requirements.txt must contain ONLY third-party packages that need to be installed using pip.
27. NEVER put Python standard-library modules into requirements.txt.
28. The following are Python standard-library modules and MUST NOT appear in requirements.txt:
    json, os, sys, re, math, time, datetime, pathlib, collections, itertools, functools, typing, logging, subprocess, threading, multiprocessing, sqlite3, csv, hashlib, uuid, random, statistics, argparse, unittest, dataclasses, enum, shutil, tempfile, urllib, socket, http, email, base64, secrets, io
29. Do NOT add "json" to requirements.txt simply because the code contains:
    import json
30. Before generating requirements.txt, inspect the imports used by the generated Python files.
31. Distinguish Python standard-library modules from third-party packages.
32. requirements.txt must contain valid installable PyPI package names only.
33. If a Python project uses only standard-library modules, do not invent dependencies.
34. Never add a package just because its name resembles a Python standard-library module.
35. For example:
    WRONG: json, os, pathlib, re, requests
    CORRECT: requests
36. If BeautifulSoup is used (from bs4 import BeautifulSoup), the dependency is: beautifulsoup4
37. If requests is used (import requests), the dependency is: requests
38. If a module is part of Python itself, it does not belong in requirements.txt.

============================================================
DEPENDENCY CONSISTENCY
======================

39. Every third-party import must have its corresponding dependency declared.
40. Every dependency declared in requirements.txt should actually be required by the generated project.
41. Do not add unused dependencies.
42. Do not confuse import names with PyPI package names.
43. Verify that generated dependency names correspond to real installable packages.
44. Keep requirements.txt minimal.

============================================================
TESTING RULES
=============

45. Tests must import the actual generated modules.
46. Tests must run using the detected environment.
47. Do not assume packages that are not declared.
48. Do not create tests for functionality that was not requested.
49. Tests must validate real behavior rather than simply checking that functions exist.

============================================================
OUTPUT REQUIREMENT
==================

Return ONLY the structured CodeGenerationResult.

Each generated file must contain:
* path
* complete content

Do not return explanations outside the structured output.
"""

    # ========================================================
    # STREAMING CALLBACK
    # ========================================================
    handler = CoderStreamHandler(project_id)

    # ========================================================
    # CALL LLM
    # ========================================================
    result = coder_llm.invoke(
        prompt,
        config={"callbacks": [handler]}
    )

    print("FINALIZING_CODE")

    # ========================================================
    # VALIDATE LLM RESULT
    # ========================================================
    if not result or not result.files:
        raise RuntimeError("Coder Agent generated no files.")

    # ========================================================
    # PROCESS GENERATED FILES
    # ========================================================
    files = {}

    for file in result.files:
        path = file.path.strip()
        content = clean_content(file.content)

        if not path:
            print("WARNING: Coder generated a file without a path. Skipping.")
            continue

        if not content:
            print(f"WARNING: Empty content generated for {path}. Skipping.")
            continue

        files[path] = content

    # ========================================================
    # FINAL VALIDATION
    # ========================================================
    if not files:
        raise RuntimeError("Coder Agent returned no valid files.")

    print(f"CODE_GENERATED: {len(files)} files")

    for path in files:
        print(f"  Generated: {path}")

    # ========================================================
    # RETURN STATE UPDATE
    # ========================================================
    return {
        "files": files,
        "status": "CODE_GENERATED",
    }