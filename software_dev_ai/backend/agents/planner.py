from llm.model import llm
from schemas.plan_schema import DevelopmentPlan
from rag import store_plan, store_conversation


planner_llm = llm.with_structured_output(DevelopmentPlan)


def planner_agent(state):

    requirement = state["user_requirement"]
    project_id = state["project_id"]

    # Store user requirement in conversation history
    try:
        store_conversation(project_id, "user", requirement)
    except Exception as e:
        print(f"Failed to store conversation: {e}")

    print("GENERATING_PLAN")

    prompt = f"""
You are the Planner Agent of an AI software development platform.

Your job is to analyze the developer's requirement and create
a clear development plan.

Developer requirement:
{requirement}

Create a development plan containing:

1. Project type
2. Recommended technologies
3. Main components
4. Development tasks
5. Testing requirements

Do NOT write the actual code.

Focus only on planning.
CRITICAL: When recommending technologies for React applications, always recommend Vite and React 18+. DO NOT recommend create-react-app (`react-scripts`) as it is deprecated.
"""

    plan = planner_llm.invoke(prompt)

    print("FINALIZING_PLAN")

    plan_dict = plan.model_dump()

    # Store plan in RAG
    try:
        store_plan(project_id, plan_dict)
    except Exception as e:
        print(f"Failed to store plan: {e}")

    print("PLANNED")

    # Return ONLY the keys that changed (LangGraph best practice)
    return {
        "plan": plan_dict,
        "status": "PLANNED",
    }