from pathlib import Path
import sqlite3

from langgraph.graph import StateGraph, END

from state.state import DevelopmentState
from agents.planner import planner_agent
from agents.coder import coder_agent
from agents.file_writer import file_writer_agent
from agents.environment import environment_agent
from agents.runtime import runtime_agent
from agents.tester import tester_agent
from agents.reviewer import reviewer_agent

MAX_ITERATIONS = 3

# ============================================================
# CONDITIONAL EDGE — AFTER FILE WRITER
# ============================================================

def after_file_writer(state: DevelopmentState) -> str:
    """
    Decide whether to continue to environment setup
    or send the project back to the coder.

    If file writing failed, there is no point trying to
    install dependencies or run tests on an incomplete project.
    """
    status = state.get("status", "")

    if status == "FILE_WRITING_FAILED":
        print("GRAPH: File writing failed → retry coder")
        iteration = state.get("iteration", 0)

        if iteration >= MAX_ITERATIONS:
            print("GRAPH: Maximum iterations reached")
            return "end"

        return "retry"

    return "continue"

# ============================================================
# CONDITIONAL EDGE — AFTER ENVIRONMENT
# ============================================================

def after_environment(state: DevelopmentState) -> str:
    """
    Decide whether the runtime environment was created
    successfully.

    If environment setup fails, send the error back to
    the coder so it can correct dependency/configuration issues.
    """
    status = state.get("status", "")

    if status == "ENVIRONMENT_SETUP_FAILED":
        print("GRAPH: Environment setup failed → retry coder")
        iteration = state.get("iteration", 0)

        if iteration >= MAX_ITERATIONS:
            print("GRAPH: Maximum iterations reached")
            return "end"

        return "retry"

    return "continue"

# ============================================================
# CONDITIONAL EDGE — AFTER RUNTIME
# ============================================================

def after_runtime(state: DevelopmentState) -> str:
    """
    Decide whether runtime preparation succeeded.

    Runtime failures are sent back to the coder because they
    may indicate incorrect dependencies or project configuration.
    """
    status = state.get("status", "")

    if status == "RUNTIME_FAILED":
        print("GRAPH: Runtime failed → retry coder")
        iteration = state.get("iteration", 0)

        if iteration >= MAX_ITERATIONS:
            print("GRAPH: Maximum iterations reached")
            return "end"

        return "retry"

    return "continue"

# ============================================================
# CONDITIONAL EDGE — AFTER TESTER
# ============================================================

def after_tester(state: DevelopmentState) -> str:
    """
    Always send test results to the reviewer.

    The reviewer decides whether the project should be
    approved or sent back for another coding iteration.
    """
    return "review"

# ============================================================
# CONDITIONAL EDGE — AFTER REVIEWER
# ============================================================

def should_retry(state: DevelopmentState) -> str:
    """
    Decide whether the reviewer approved the project
    or whether another coding iteration is required.
    """
    review = state.get("review_result", "")
    iteration = state.get("iteration", 0)

    # --------------------------------------------------------
    # APPROVED
    # --------------------------------------------------------
    if review == "APPROVED":
        print("GRAPH: Reviewer approved → END")
        return "end"

    # --------------------------------------------------------
    # MAX ITERATIONS
    # --------------------------------------------------------
    if iteration >= MAX_ITERATIONS:
        print(f"GRAPH: Maximum iterations ({MAX_ITERATIONS}) reached → END")
        return "end"

    # --------------------------------------------------------
    # REVISION REQUIRED
    # --------------------------------------------------------
    print(f"GRAPH: Reviewer requested revision → coder (iteration {iteration})")
    return "retry"

# ============================================================
# CHECKPOINTER
# ============================================================

def _get_checkpointer():
    """
    Create a persistent SQLite checkpointer.

    This allows LangGraph state to survive server restarts.

    If the SQLite checkpointer package is unavailable,
    MemorySaver is used as a fallback.
    """
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        db_path = (
            Path(__file__).resolve().parents[1]
            / "instance"
            / "langgraph_checkpoints.db"
        )

        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        return SqliteSaver(conn)

    except ImportError:
        print("WARNING: langgraph.checkpoint.sqlite not available.")
        print("Falling back to MemorySaver. State will be lost after server restart.")

        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

# ============================================================
# APPROVAL BREAKPOINT
# ============================================================

def wait_for_approval_node(state: DevelopmentState) -> dict:
    """
    Dummy node used as the plan approval breakpoint.

    LangGraph interrupts before this node executes.

    After the user approves the plan, the graph resumes
    from this point and continues to the coder.
    """
    print("PLAN_APPROVED")
    return {
        "status": "PLAN_APPROVED"
    }



def build_graph():
    """
    Construct and compile the multi-agent development graph.
    """
    workflow = StateGraph(DevelopmentState)

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------
    workflow.add_node("planner", planner_agent)
    workflow.add_node("wait_for_approval", wait_for_approval_node)
    workflow.add_node("coder", coder_agent)
    workflow.add_node("file_writer", file_writer_agent)
    workflow.add_node("environment", environment_agent)
    workflow.add_node("runtime", runtime_agent)
    workflow.add_node("tester", tester_agent)
    workflow.add_node("reviewer", reviewer_agent)

    workflow.set_entry_point("planner")

    
    workflow.add_edge("planner", "wait_for_approval")

    workflow.add_edge("wait_for_approval", "coder")

    
    workflow.add_edge("coder", "file_writer")

    
    workflow.add_conditional_edges(
        "file_writer",
        after_file_writer,
        {
            "continue": "environment",
            "retry": "coder",
            "end": END,
        },
    )

  
    workflow.add_conditional_edges(
        "environment",
        after_environment,
        {
            "continue": "runtime",
            "retry": "coder",
            "end": END,
        },
    )

   
    workflow.add_conditional_edges(
        "runtime",
        after_runtime,
        {
            "continue": "tester",
            "retry": "coder",
            "end": END,
        },
    )

    
    workflow.add_edge("tester", "reviewer")

   
    workflow.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "retry": "coder",
            "end": END,
        },
    )

    
    checkpointer = _get_checkpointer()

    # Interrupt ONLY before approval.
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["wait_for_approval"],
    )

dev_graph = build_graph()