from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
import os
import uuid
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY
)

try:
    from backend.Agent.prompts import *
    from backend.Agent.states import *
    from backend.Agent.tools import write_file, read_file, get_current_directory, list_files, file_exists
except ModuleNotFoundError:
    from Agent.prompts import *
    from Agent.states import *
    from Agent.tools import write_file, read_file, get_current_directory, list_files, file_exists

_ = load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")  # Use supported model

def planner_agent(state: dict) -> dict:
    """Planner agent that uses LLM to create a detailed plan."""
    user_prompt = state["user_prompt"]

    prompt = planner_prompt(user_prompt)
    response = llm.invoke([{"role": "user", "content": prompt}])

    # Parse the response to create Plan object
    # For simplicity, assume the LLM returns structured text, but in practice, use better parsing
    plan_text = response.content

    # Generate clean project name from prompt
    import re
    project_name = re.sub(r'[^a-zA-Z0-9\s]', '', user_prompt.lower())
    project_name = re.sub(r'\b(create|simple|web|app|with)\b', '', project_name)
    project_name = re.sub(r'\s+', '-', project_name.strip())
    project_name = project_name.strip('-')[:20]

    if not project_name:
        project_name = "webapp"

    # Create project folder path
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspaces"))
    unique_id = str(uuid.uuid4())[:8]
    project_folder = os.path.join(BASE_DIR, f"{project_name}-{unique_id}").replace("\\", "/")

    # Create a plan structure based on LLM response
    plan = Plan(
        name=project_name,
        description=f"Web application based on: {user_prompt}",
        techstack="html, css, javascript",
        features=["HTML structure", "CSS styling", "JavaScript functionality"],
        files=[
            File(path=f"{project_folder}/index.html", purpose="Main HTML file"),
            File(path=f"{project_folder}/style.css", purpose="CSS styling"),
            File(path=f"{project_folder}/script.js", purpose="JavaScript functionality")
        ]
    )

    print(f"Created plan: {plan.name} in {project_folder}")
    return {"plan": plan}

def architect_agent(state: dict) -> dict:
    """Architect that uses LLM to create implementation tasks."""
    plan = state["plan"]

    # Extract project folder from first file path
    project_folder = "/".join(plan.files[0].path.split("/")[:-1])

    prompt = architect_prompt(plan.description)
    response = llm.invoke([{"role": "user", "content": prompt}])

    # For simplicity, still create hardcoded tasks, but in practice parse LLM response
    tasks = [
        ImplementationTask(
            filepath=f"{project_folder}/index.html",
            task_description="Create HTML structure with proper DOCTYPE, head, and body. Include links to style.css and script.js.",
            dependencies=[]
        ),
        ImplementationTask(
            filepath=f"{project_folder}/style.css",
            task_description="Create CSS styling for the application with responsive design and modern appearance.",
            dependencies=[f"{project_folder}/index.html"]
        ),
        ImplementationTask(
            filepath=f"{project_folder}/script.js",
            task_description="Create JavaScript functionality for the application with proper event handling.",
            dependencies=[f"{project_folder}/index.html", f"{project_folder}/style.css"]
        )
    ]

    task_plan = TaskPlan(implementation_steps=tasks)
    task_plan.plan = plan

    print(f"Created {len(tasks)} implementation tasks in {project_folder}")
    return {"task_plan": task_plan}

def coder_agent(state: dict) -> dict:
    """Coder agent that creates files with proper prompts and file reading."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        print(f"Completed all {len(steps)} tasks")
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    print(f"Working on: {current_task.filepath}")

    # Read dependency files
    dependency_contents = ""
    for dep in current_task.dependencies:
        if file_exists.invoke({"path": dep}) == "true":
            content = read_file.invoke({"path": dep})
            dependency_contents += f"\n--- Content of {dep} ---\n{content}\n"

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Create {current_task.filepath} for: {coder_state.task_plan.plan.description}\n"
        f"Task: {current_task.task_description}\n"
        f"Dependencies:{dependency_contents}\n"
        "Write complete file content using write_file(path, content)."
    )

    coder_tools = [write_file, read_file, file_exists]
    react_agent = create_react_agent(llm, coder_tools)

    try:
        result = react_agent.invoke({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        })

        # Check if file was created
        if file_exists.invoke({"path": current_task.filepath}) == "true":
            coder_state.created_files.append(current_task.filepath)
            print(f"Successfully created {current_task.filepath}")
        else:
            print(f"Failed to create {current_task.filepath}")

    except Exception as e:
        print(f"Error: {e}")

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
    {"END": END, "coder": "coder"}
)

graph.set_entry_point("planner")
agent = graph.compile()

if __name__ == "__main__":
    result = agent.invoke(
        {"user_prompt": "Create a simple todo list app"},
        {"recursion_limit": 20}
    )
    print("Final State:", result)
