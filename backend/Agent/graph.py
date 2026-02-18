import os
import json
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


# ---------------------------------------------------
# Setup
# ---------------------------------------------------

_ = load_dotenv()
set_debug(False)
set_verbose(False)

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
    return llm is not None, MODEL_NAME, _LLM_INIT_ERROR


def _clean_json(content: str):
    content = content.strip()
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "")
    return content.strip()


def _validate_index_exists(steps):
    if not steps:
        raise RuntimeError("No implementation steps generated.")

    project_folder = os.path.dirname(steps[0].filepath)
    index_path = os.path.join(project_folder, "index.html")

    if not os.path.exists(index_path):
        raise RuntimeError("Runnable app was not created (missing index.html).")


def _normalize_task_filepaths(task_plan: TaskPlan, plan: Plan) -> TaskPlan:
    """Map architect output to project-scoped file paths from the plan."""
    planned_paths = [file.path.strip() for file in plan.files if file.path.strip()]
    if not planned_paths:
        return task_plan

    normalized_planned = {
        os.path.normpath(path).replace("\\", "/") for path in planned_paths
    }
    planned_by_name = {
        os.path.basename(os.path.normpath(path)): os.path.normpath(path).replace("\\", "/")
        for path in planned_paths
    }
    base_folder = os.path.dirname(os.path.normpath(planned_paths[0]))

    def _normalize(path: str) -> str:
        cleaned = (path or "").strip()
        if not cleaned:
            return cleaned
        normalized = os.path.normpath(cleaned).replace("\\", "/")
        if normalized in normalized_planned:
            return normalized

        by_name = planned_by_name.get(os.path.basename(os.path.normpath(cleaned)))
        if by_name:
            return by_name

        if os.path.isabs(cleaned):
            return normalized

        prefixed = os.path.join(base_folder, cleaned)
        return os.path.normpath(prefixed).replace("\\", "/")

    for step in task_plan.implementation_steps:
        step.filepath = _normalize(step.filepath)
        step.dependencies = [_normalize(dep) for dep in step.dependencies]

    return task_plan


# ---------------------------------------------------
# PLANNER
# ---------------------------------------------------

def planner_agent(state: dict) -> dict:
    user_prompt = state["user_prompt"]

    response = _require_llm().invoke(
        f"""
You are the PLANNER agent.

Return ONLY valid JSON matching:

{{
  "name": "string",
  "description": "string",
  "techstack": "html, css, javascript",
  "features": ["string"],
  "files": [
    {{"path": "project/index.html", "purpose": "Main HTML file"}},
    {{"path": "project/style.css", "purpose": "Styling"}},
    {{"path": "project/script.js", "purpose": "JS logic"}}
  ]
}}

User Request:
{user_prompt}

Return JSON only. No explanation.
"""
    )

    data = json.loads(_clean_json(response.content))
    plan = Plan(**data)

    return {"plan": plan}


# ---------------------------------------------------
# ARCHITECT
# ---------------------------------------------------

def architect_agent(state: dict) -> dict:
    plan: Plan = state["plan"]

    response = _require_llm().invoke(
        f"""
You are the ARCHITECT agent.

Create implementation tasks for EXACTLY these files:
- index.html
- style.css
- script.js

Return ONLY JSON:

{{
  "implementation_steps": [
    {{
      "filepath": "string",
      "task_description": "string",
      "dependencies": []
    }}
  ]
}}

Project Plan:
{plan.model_dump_json()}

Return JSON only.
"""
    )

    data = json.loads(_clean_json(response.content))
    task_plan = TaskPlan(**data)
    task_plan = _normalize_task_filepaths(task_plan, plan)

    task_plan.plan = plan

    return {"task_plan": task_plan}


# ---------------------------------------------------
# CODER
# ---------------------------------------------------

def coder_agent(state: dict) -> dict:
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(
            task_plan=state["task_plan"],
            current_step_idx=0
        )

    steps = coder_state.task_plan.implementation_steps

    if coder_state.current_step_idx >= len(steps):
        _validate_index_exists(steps)
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]

    system_prompt = coder_system_prompt()

    response = _require_llm().invoke([
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"""
Task:
{current_task.task_description}

Return ONLY full file content.
No markdown.
No explanation.
"""
        }
    ])

    content = response.content.strip()

    print("Writing:", current_task.filepath)

    write_result = write_file.invoke({
        "path": current_task.filepath,
        "content": content
    })
    if isinstance(write_result, str) and write_result.startswith("Error writing file:"):
        coder_state.failed_files.append(current_task.filepath)
    else:
        coder_state.created_files.append(current_task.filepath)

    coder_state.current_step_idx += 1

    status = "DONE" if coder_state.current_step_idx >= len(steps) else "RUNNING"

    if status == "DONE":
        _validate_index_exists(steps)

    return {"coder_state": coder_state, "status": status}


# ---------------------------------------------------
# GRAPH
# ---------------------------------------------------

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


# ---------------------------------------------------
# RUN TEST
# ---------------------------------------------------

if __name__ == "__main__":
    result = agent.invoke(
        {"user_prompt": "Build a colourful modern todo app in html css and js"},
        {"recursion_limit": 15},
    )
    print("Final State:", result)
