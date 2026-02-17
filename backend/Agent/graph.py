import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from hashlib import sha256
import time

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
_MAX_CODER_WORKERS = max(1, int(os.getenv("CODER_MAX_WORKERS", "2")))
_MAX_DEPENDENCY_CHARS = max(500, int(os.getenv("CODER_DEP_CONTEXT_CHARS", "3500")))
_FILE_CONTENT_CACHE_MAX = max(10, int(os.getenv("FILE_CONTENT_CACHE_MAX", "200")))
_FILE_CONTENT_CACHE: dict[str, str] = {}
_FILE_CONTENT_CACHE_LOCK = Lock()
_LLM_MAX_RETRIES = max(1, int(os.getenv("LLM_MAX_RETRIES", "3")))
_LLM_RETRY_DELAY_SECONDS = max(1, int(os.getenv("LLM_RETRY_DELAY_SECONDS", "2")))
_FALLBACK_BANNER = "Fallback build: generated without LLM response."

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


def _cache_get(key: str) -> str | None:
    with _FILE_CONTENT_CACHE_LOCK:
        value = _FILE_CONTENT_CACHE.get(key)
        if value and _FALLBACK_BANNER in value:
            _FILE_CONTENT_CACHE.pop(key, None)
            return None
        return value


def _cache_set(key: str, value: str) -> None:
    with _FILE_CONTENT_CACHE_LOCK:
        if len(_FILE_CONTENT_CACHE) >= _FILE_CONTENT_CACHE_MAX:
            oldest_key = next(iter(_FILE_CONTENT_CACHE))
            _FILE_CONTENT_CACHE.pop(oldest_key, None)
        _FILE_CONTENT_CACHE[key] = value


def _file_cache_key(app_description: str, filepath: str, task_description: str) -> str:
    signature = "|".join(
        [
            app_description.strip().lower(),
            os.path.basename(filepath).lower(),
            task_description.strip().lower(),
        ]
    )
    return sha256(signature.encode("utf-8")).hexdigest()


def _read_dependency_context(dependencies: list[str]) -> str:
    chunks: list[str] = []
    total = 0
    for dep in dependencies:
        if file_exists.invoke({"path": dep}) != "true":
            continue
        content = read_file.invoke({"path": dep})
        if content.startswith("Error reading file:"):
            continue
        remaining = _MAX_DEPENDENCY_CHARS - total
        if remaining <= 0:
            break
        snippet = content[:remaining]
        chunks.append(f"\n[{os.path.basename(dep)}]\n{snippet}")
        total += len(snippet)
    return "".join(chunks)


def _invoke_llm_for_task(app_description: str, task: ImplementationTask) -> str:
    system_prompt = coder_system_prompt()
    dependency_context = _read_dependency_context(task.dependencies)
    user_prompt = (
        f"App goal: {app_description}\n"
        f"Target file: {task.filepath}\n"
        f"Task: {task.task_description}\n"
        "If dependencies are provided, keep naming and IDs consistent.\n"
        f"Dependency context:{dependency_context}\n"
        "Output only the complete file content."
    )
    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return _strip_code_fences(response.content)


def _invoke_llm_with_retry(app_description: str, task: ImplementationTask) -> str:
    last_error: Exception | None = None
    for attempt in range(1, _LLM_MAX_RETRIES + 1):
        try:
            content = _invoke_llm_for_task(app_description, task)
            if content.strip():
                return content
            raise RuntimeError("LLM returned empty content.")
        except Exception as e:
            last_error = e
            if attempt < _LLM_MAX_RETRIES:
                time.sleep(_LLM_RETRY_DELAY_SECONDS)
    raise RuntimeError(f"LLM generation failed for {task.filepath}: {last_error}")


def _generate_and_write_file(app_description: str, task: ImplementationTask) -> tuple[str, bool]:
    cache_key = _file_cache_key(app_description, task.filepath, task.task_description)
    cached = _cache_get(cache_key)
    file_content = cached

    if file_content is None:
        file_content = _invoke_llm_with_retry(app_description, task)
        _cache_set(cache_key, file_content)

    write_result = write_file.invoke({"path": task.filepath, "content": file_content})
    ok = write_result.startswith("Successfully wrote") and file_exists.invoke({"path": task.filepath}) == "true"
    return task.filepath, ok


def planner_agent(state: dict) -> dict:
    """Planner creates a deterministic file plan quickly (no LLM round-trip)."""
    user_prompt = state["user_prompt"]
    project_name = _project_name_from_prompt(user_prompt)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspaces"))
    unique_id = str(uuid.uuid4())[:8]
    project_folder = os.path.join(base_dir, f"{project_name}-{unique_id}").replace("\\", "/")
    os.makedirs(project_folder, exist_ok=True)

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
            dependencies=[],
        ),
        ImplementationTask(
            filepath=f"{project_folder}/script.js",
            task_description="Create complete JavaScript functionality based on the requested app behavior.",
            dependencies=[f"{project_folder}/index.html"],
        ),
    ]

    task_plan = TaskPlan(implementation_steps=tasks)
    task_plan.plan = plan

    print(f"Created {len(tasks)} implementation tasks in {project_folder}")
    return {"task_plan": task_plan}


def coder_agent(state: dict) -> dict:
    """Coder batches work to reduce recursion and parallelizes independent file generation."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    start_idx = coder_state.current_step_idx
    if start_idx >= len(steps):
        print(f"Completed all {len(steps)} tasks")
        return {"coder_state": coder_state, "status": "DONE"}

    app_description = coder_state.task_plan.plan.description

    # Phase 1: dependency root file(s) serially (currently index.html).
    for current_task in steps[start_idx:]:
        if current_task.dependencies:
            continue
        if os.path.basename(current_task.filepath).lower() != "index.html":
            continue
        print(f"Working on base file: {current_task.filepath}")
        try:
            filepath, ok = _generate_and_write_file(app_description, current_task)
            if ok:
                coder_state.created_files.append(filepath)
                print(f"Successfully created {filepath}")
            else:
                coder_state.failed_files.append(filepath)
                print(f"Failed to create {filepath}")
        except Exception as e:
            coder_state.failed_files.append(current_task.filepath)
            print(f"Error creating {current_task.filepath}: {e}")

    # Phase 2: generate remaining files in parallel when possible.
    pending_tasks = [
        task
        for task in steps[start_idx:]
        if task.filepath not in coder_state.created_files and task.filepath not in coder_state.failed_files
    ]
    if pending_tasks:
        worker_count = min(_MAX_CODER_WORKERS, len(pending_tasks))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(_generate_and_write_file, app_description, task): task
                for task in pending_tasks
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    filepath, ok = future.result()
                    if ok:
                        coder_state.created_files.append(filepath)
                        print(f"Successfully created {filepath}")
                    else:
                        coder_state.failed_files.append(filepath)
                        print(f"Failed to create {filepath}")
                except Exception as e:
                    coder_state.failed_files.append(task.filepath)
                    print(f"Error creating {task.filepath}: {e}")

    coder_state.current_step_idx = len(steps)
    print(f"Completed all {len(steps)} tasks")
    return {"coder_state": coder_state, "status": "DONE"}


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
