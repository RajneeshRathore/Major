"""
RAG — Project Memory (ChromaDB)

Stores and retrieves:
 • Project files and their contents
 • Previous conversations / chat history
 • Test results
 • Documentation and project context

All agents can query this memory for relevant context before acting.
"""

import os
import chromadb
from chromadb.config import Settings
from pathlib import Path


# ─────────────────────────────────────────────
# CHROMADB CLIENT
# ─────────────────────────────────────────────

CHROMA_DIR = Path(__file__).resolve().parents[1] / "chroma_data"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
    settings=Settings(anonymized_telemetry=False),
)


# ─────────────────────────────────────────────
# COLLECTIONS
# ─────────────────────────────────────────────

def _get_project_collection(project_id: str):
    """Get or create a ChromaDB collection for a specific project."""
    return client.get_or_create_collection(
        name=f"project_{project_id}",
        metadata={"hnsw:space": "cosine"},
    )


def _get_conversation_collection():
    """Get or create a collection for storing all conversations."""
    return client.get_or_create_collection(
        name="conversations",
        metadata={"hnsw:space": "cosine"},
    )


# ─────────────────────────────────────────────
# STORE PROJECT FILES
# ─────────────────────────────────────────────

def store_project_files(project_id: str, files: dict[str, str]):
    """
    Store all generated files of a project into ChromaDB.

    Args:
        project_id: Unique project identifier.
        files: Dict mapping file paths to their contents.
    """

    collection = _get_project_collection(project_id)

    ids = []
    documents = []
    metadatas = []

    for file_path, content in files.items():
        doc_id = f"{project_id}::{file_path}"
        ids.append(doc_id)
        documents.append(content)
        metadatas.append({
            "project_id": project_id,
            "file_path": file_path,
            "type": "source_file",
        })

    if ids:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )


# ─────────────────────────────────────────────
# STORE TEST RESULTS
# ─────────────────────────────────────────────

def store_test_results(project_id: str, test_result: dict):
    """Store test results for a project."""

    collection = _get_project_collection(project_id)

    import json
    doc_id = f"{project_id}::test_result"
    doc_text = json.dumps(test_result, indent=2)

    collection.upsert(
        ids=[doc_id],
        documents=[doc_text],
        metadatas=[{
            "project_id": project_id,
            "type": "test_result",
        }],
    )


# ─────────────────────────────────────────────
# STORE PLAN
# ─────────────────────────────────────────────

def store_plan(project_id: str, plan: dict):
    """Store the development plan."""

    collection = _get_project_collection(project_id)

    import json
    doc_id = f"{project_id}::plan"
    doc_text = json.dumps(plan, indent=2)

    collection.upsert(
        ids=[doc_id],
        documents=[doc_text],
        metadatas=[{
            "project_id": project_id,
            "type": "plan",
        }],
    )


# ─────────────────────────────────────────────
# STORE CONVERSATION MESSAGE
# ─────────────────────────────────────────────

def store_conversation(project_id: str, role: str, content: str):
    """
    Store a single conversation message.

    Args:
        project_id: The project this conversation belongs to.
        role: 'user' or 'agent'.
        content: The message text.
    """
    import uuid

    collection = _get_conversation_collection()

    doc_id = f"{project_id}::msg::{uuid.uuid4().hex[:8]}"

    collection.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[{
            "project_id": project_id,
            "role": role,
            "type": "conversation",
        }],
    )


# ─────────────────────────────────────────────
# RETRIEVE RELEVANT CONTEXT
# ─────────────────────────────────────────────

def retrieve_context(project_id: str, query: str, n_results: int = 5) -> list[dict]:
    """
    Query the project's ChromaDB collection for relevant context.

    Args:
        project_id: The project to search in.
        query: The search query (e.g., the user requirement).
        n_results: Max number of results to return.

    Returns:
        A list of dicts with 'document', 'metadata', and 'distance'.
    """

    collection = _get_project_collection(project_id)

    # If collection is empty, return nothing
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
    )

    context_items = []

    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            context_items.append({
                "document": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })

    return context_items


# ─────────────────────────────────────────────
# RETRIEVE CONVERSATION HISTORY
# ─────────────────────────────────────────────

def retrieve_conversation_history(project_id: str, n_results: int = 20) -> list[dict]:
    """
    Retrieve past conversation messages for a project.

    Args:
        project_id: The project whose history to retrieve.
        n_results: Max messages to return.

    Returns:
        List of dicts with 'role' and 'content'.
    """

    collection = _get_conversation_collection()

    if collection.count() == 0:
        return []

    results = collection.get(
        where={"project_id": project_id},
        limit=n_results,
    )

    messages = []

    if results and results["documents"]:
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            messages.append({
                "role": meta.get("role", "unknown"),
                "content": doc,
            })

    return messages
