from pathlib import Path
from tools.file_tools import write_file
from rag import store_project_files


def file_writer_agent(state):
    """Write all generated files from the coder agent to the project directory and store in RAG."""

    project_id = state["project_id"]
    files = state.get("files", {})

    print("WRITING_FILES")

    written = []

    for file_path, content in files.items():
        result = write_file(
            project_id,
            file_path,
            content
        )
        written.append(result)
        print(f"  Created: {result}")

    # Store files in ChromaDB
    try:
        if files:
            store_project_files(project_id, files)
            print("  Files stored in ChromaDB memory")
    except Exception as e:
        print(f"  Failed to store files in ChromaDB: {e}")

    print("FILES_WRITTEN")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "status": "FILES_WRITTEN",
    }
