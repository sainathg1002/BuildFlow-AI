import os
import re
import uuid

from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if GROQ_API_KEY:
    llm = ChatGroq(model="openai/gpt-oss-120b", api_key=GROQ_API_KEY)
else:
    llm = ChatGroq(model="openai/gpt-oss-120b")

try:
    from backend.Agent.prompts import coder_system_prompt
    from backend.Agent.states import CoderState, File, ImplementationTask, Plan, TaskPlan
    from backend.Agent.tools import file_exists, read_file, write_file
except ModuleNotFoundError:
    from Agent.prompts import coder_system_prompt
    from Agent.states import CoderState, File, ImplementationTask, Plan, TaskPlan
    from Agent.tools import file_exists, read_file, write_file


def _project_name_from_prompt(user_prompt: str) -> str:
    project_name = re.sub(r"[^a-zA-Z0-9\s]", "", user_prompt.lower())
    project_name = re.sub(r"\b(create|simple|web|app|with)\b", "", project_name)
    project_name = re.sub(r"\s+", "-", project_name.strip())
    project_name = project_name.strip("-")[:20]
    return project_name or "webapp"


def _strip_code_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def planner_agent(state: dict) -> dict:
    """Planner creates a deterministic file plan quickly (no LLM round-trip)."""
    user_prompt = state["user_prompt"]
    project_name = _project_name_from_prompt(user_prompt)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspaces"))
    unique_id = str(uuid.uuid4())[:8]
    project_folder = os.path.join(base_dir, f"{project_name}-{unique_id}").replace("\\", "/")

    plan = Plan(
        name=project_name,
        description=f"Web application based on: {user_prompt}",
        techstack="html, css, javascript",
        features=["HTML structure", "CSS styling", "JavaScript functionality"],
        files=[
            File(path=f"{project_folder}/index.html", purpose="Main HTML file"),
            File(path=f"{project_folder}/style.css", purpose="CSS styling"),
            File(path=f"{project_folder}/script.js", purpose="JavaScript functionality"),
        ],
    )

    print(f"Created plan: {plan.name} in {project_folder}")
    return {"plan": plan}


def architect_agent(state: dict) -> dict:
    """Architect creates the file task list without extra LLM calls."""
    plan = state["plan"]
    project_folder = "/".join(plan.files[0].path.split("/")[:-1])

    tasks = [
        ImplementationTask(
            filepath=f"{project_folder}/index.html",
            task_description="Create complete HTML structure and include style.css and script.js.",
            dependencies=[],
        ),
        ImplementationTask(
            filepath=f"{project_folder}/style.css",
            task_description="Create complete CSS styling with responsive layout and clear visual hierarchy.",
            dependencies=[f"{project_folder}/index.html"],
        ),
        ImplementationTask(
            filepath=f"{project_folder}/script.js",
            task_description="Create complete JavaScript functionality based on the requested app behavior.",
            dependencies=[f"{project_folder}/index.html", f"{project_folder}/style.css"],
        ),
    ]

    task_plan = TaskPlan(implementation_steps=tasks)
    task_plan.plan = plan

    print(f"Created {len(tasks)} implementation tasks in {project_folder}")
    return {"task_plan": task_plan}


def coder_agent(state: dict) -> dict:
    """Coder creates each file with one direct LLM call and writes it immediately."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        print(f"Completed all {len(steps)} tasks")
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    print(f"Working on: {current_task.filepath}")

    dependency_contents = ""
    for dep in current_task.dependencies:
        if file_exists.invoke({"path": dep}) == "true":
            content = read_file.invoke({"path": dep})
            dependency_contents += f"\n--- Content of {dep} ---\n{content}\n"

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Build this app: {coder_state.task_plan.plan.description}\n"
        f"Now create file: {current_task.filepath}\n"
        f"Task: {current_task.task_description}\n"
        f"Dependencies:\n{dependency_contents}\n"
        "Return ONLY the full file content. No markdown fences, no explanations."
    )

    try:
        response = llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        file_content = _strip_code_fences(response.content)
        write_result = write_file.invoke({"path": current_task.filepath, "content": file_content})

        if write_result.startswith("Successfully wrote") and file_exists.invoke({"path": current_task.filepath}) == "true":
            coder_state.created_files.append(current_task.filepath)
            print(f"Successfully created {current_task.filepath}")
        else:
            coder_state.failed_files.append(current_task.filepath)
            print(f"Failed to create {current_task.filepath}: {write_result}")
    except Exception as e:
        coder_state.failed_files.append(current_task.filepath)
        print(f"Error creating {current_task.filepath}: {e}")

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state}


# Build the graph
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
        {"user_prompt": "Create a simple todo list app"},
        {"recursion_limit": 20},
    )
    print("Final State:", result)
