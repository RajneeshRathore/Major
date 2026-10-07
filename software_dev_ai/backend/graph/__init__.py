from langgraph.graph import StateGraph, END

from state.state import DevelopmentState
from agents.planner import planner_agent
from agents.coder import coder_agent
from agents.file_writer import file_writer_agent
from agents.environment import environment_agent
from agents.runtime import runtime_agent
from agents.tester import tester_agent
from agents.reviewer import reviewer_agent


# ─────────────────────────────────────────────
# CONDITIONAL EDGES
# ─────────────────────────────────────────────

def should_retry(state: DevelopmentState) -> str:
    """After the reviewer decides, either loop back to the coder or finish."""

    review = state.get("review_result", "")
    iteration = state.get("iteration", 0)

    # Hard cap on iterations to prevent infinite loops
    if iteration >= 3:
        return "end"

    if review == "APPROVED":
        return "end"

    return "retry"


# ─────────────────────────────────────────────
# CHECKPOINTER — Use SqliteSaver for persistence
# ─────────────────────────────────────────────

from pathlib import Path

def _get_checkpointer():
    """Create a persistent SQLite checkpointer so state survives server restarts."""
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3

        db_path = Path(__file__).resolve().parents[1] / "instance" / "langgraph_checkpoints.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        return SqliteSaver(conn)
    except ImportError:
        # Fallback to MemorySaver if sqlite saver is not available
        print("WARNING: langgraph.checkpoint.sqlite not available, falling back to MemorySaver (state will be lost on restart)")
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()


# ─────────────────────────────────────────────
# BUILD THE GRAPH
# ─────────────────────────────────────────────

def wait_for_approval_node(state: DevelopmentState) -> dict:
    """Dummy node to act as a breakpoint after planning."""
    return {}

def build_graph():
    """Construct and compile the multi-agent development graph."""

    workflow = StateGraph(DevelopmentState)

    # --- Add nodes ---
    workflow.add_node("planner", planner_agent)
    workflow.add_node("wait_for_approval", wait_for_approval_node)
    workflow.add_node("coder", coder_agent)
    workflow.add_node("file_writer", file_writer_agent)
    workflow.add_node("environment", environment_agent)
    workflow.add_node("runtime", runtime_agent)
    workflow.add_node("tester", tester_agent)
    workflow.add_node("reviewer", reviewer_agent)

    # --- Linear edges ---
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "wait_for_approval")
    workflow.add_edge("wait_for_approval", "coder")
    workflow.add_edge("coder", "file_writer")
    workflow.add_edge("file_writer", "environment")
    workflow.add_edge("environment", "runtime")
    workflow.add_edge("runtime", "tester")
    workflow.add_edge("tester", "reviewer")

    # --- Conditional edge after reviewer ---
    workflow.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "retry": "coder",
            "end": END,
        },
    )

    checkpointer = _get_checkpointer()
    # Interrupt ONLY before wait_for_approval, so retries don't pause!
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["wait_for_approval"])


# Pre-built compiled graph ready to be invoked
dev_graph = build_graph()
