import os

from dotenv import load_dotenv
from langchain_core.globals import set_debug, set_verbose
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph

try:
    from backend.Agent.prompts import architect_prompt, coder_system_prompt, planner_prompt
    from backend.Agent.states import CoderState, Plan, TaskPlan
    from backend.Agent.tools import write_file
except ModuleNotFoundError:
    from Agent.prompts import architect_prompt, coder_system_prompt, planner_prompt
    from Agent.states import CoderState, Plan, TaskPlan
    from Agent.tools import write_file

_ = load_dotenv()
set_debug(True)
set_verbose(True)

MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
_LLM_INIT_ERROR = ""

if GROQ_API_KEY:
    try:
        llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
    except Exception as exc:
        llm = None
        _LLM_INIT_ERROR = str(exc)
else:
    llm = None
    _LLM_INIT_ERROR = "GROQ_API_KEY is not set."


def _require_llm() -> ChatGroq:
    if llm is None:
        raise RuntimeError(
            f"ChatGroq initialization failed for model '{MODEL_NAME}'. {_LLM_INIT_ERROR}"
        )
    return llm


def get_llm_status() -> tuple[bool, str, str]:
    """Expose LLM readiness for API pre-checks."""
    return llm is not None, MODEL_NAME, _LLM_INIT_ERROR


def _prefix_task_filepaths(task_plan: TaskPlan, base_folder: str) -> TaskPlan:
    """Ensure architect tasks point to project-scoped file paths."""
    if not base_folder:
        return task_plan

    normalized_base = os.path.normpath(base_folder)

    def _normalize_path(path: str) -> str:
        clean = path.strip()
        if not clean:
            return clean
        if os.path.isabs(clean):
            return os.path.normpath(clean).replace("\\", "/")
        prefixed = os.path.join(normalized_base, clean)
        return os.path.normpath(prefixed).replace("\\", "/")

    for step in task_plan.implementation_steps:
        step.filepath = _normalize_path(step.filepath)
        step.dependencies = [_normalize_path(dep) for dep in step.dependencies]

    return task_plan


def _validate_runnable_output(steps) -> None:
    if not steps:
        raise RuntimeError("No implementation steps found.")
    project_folder = os.path.dirname(steps[0].filepath)
    if not os.path.exists(os.path.join(project_folder, "index.html")):
        raise RuntimeError("Runnable app was not created (missing index.html).")


def planner_agent(state: dict) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state["user_prompt"]
    resp = _require_llm().with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")
    return {"plan": resp}


def architect_agent(state: dict) -> dict:
    """Creates TaskPlan from Plan."""
    plan: Plan = state["plan"]
    resp = _require_llm().with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=plan.model_dump_json())
    )
    if resp is None:
        raise ValueError("Architect did not return a valid response.")

    plan_dirs = [os.path.dirname(file.path) for file in plan.files if os.path.dirname(file.path)]
    base_folder = plan_dirs[0] if plan_dirs else ""
    resp = _prefix_task_filepaths(resp, base_folder)

    resp.plan = plan
    print(resp.model_dump_json())
    return {"task_plan": resp}


def coder_agent(state: dict) -> dict:
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps

    if coder_state.current_step_idx >= len(steps):
        _validate_runnable_output(steps)
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]

    llm_instance = _require_llm()

    system_prompt = coder_system_prompt()
    user_prompt = f"""
Task Description:
{current_task.task_description}

Return ONLY the complete file content.
No markdown.
No explanation.
"""

    response = llm_instance.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    print("Writing file:", current_task.filepath)
    write_file.invoke({"path": current_task.filepath, "content": response.content})

    coder_state.current_step_idx += 1
    status = "DONE" if coder_state.current_step_idx >= len(steps) else "RUNNING"
    if status == "DONE":
        _validate_runnable_output(steps)

    return {"coder_state": coder_state, "status": status}


graph = StateGraph(dict)
graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "END" if s.get("status") == "DONE" else "coder",
    {"END": END, "coder": "coder"},
)

graph.set_entry_point("planner")
agent = graph.compile()

if __name__ == "__main__":
    result = agent.invoke(
        {"user_prompt": "Build a colourful modern todo app in html css and js"},
        {"recursion_limit": 15},
    )
    print("Final State:", result)
