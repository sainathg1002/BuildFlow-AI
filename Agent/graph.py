from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
import os

from Agent.prompts import *
from Agent.states import *
from Agent.tools import write_file, read_file, get_current_directory, list_files, file_exists

_ = load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")  # Use supported model

def planner_agent(state: dict) -> dict:
    """Simple planner that creates a basic plan."""
    user_prompt = state["user_prompt"]
    
    # Generate clean project name from prompt
    import re
    project_name = re.sub(r'[^a-zA-Z0-9\s]', '', user_prompt.lower())
    project_name = re.sub(r'\b(create|simple|web|app|with)\b', '', project_name)
    project_name = re.sub(r'\s+', '-', project_name.strip())
    project_name = project_name.strip('-')[:20]
    
    if not project_name:
        project_name = "webapp"
    
    # Create project folder path
    project_folder = f"generated-projects/{project_name}"
    
    # Create a simple plan structure
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
    """Simple architect that creates implementation tasks."""
    plan = state["plan"]
    
    # Extract project folder from first file path
    project_folder = "/".join(plan.files[0].path.split("/")[:-1])
    
    # Create simple implementation tasks
    tasks = [
        ImplementationTask(
            filepath=f"{project_folder}/index.html",
            task_description="Create HTML structure with proper DOCTYPE, head, and body. Include links to style.css and script.js."
        ),
        ImplementationTask(
            filepath=f"{project_folder}/style.css", 
            task_description="Create CSS styling for the application with responsive design and modern appearance."
        ),
        ImplementationTask(
            filepath=f"{project_folder}/script.js",
            task_description="Create JavaScript functionality for the application with proper event handling."
        )
    ]
    
    task_plan = TaskPlan(implementation_steps=tasks)
    task_plan.plan = plan
    
    print(f"Created {len(tasks)} implementation tasks in {project_folder}")
    return {"task_plan": task_plan}

def coder_agent(state: dict) -> dict:
    """Simple coder agent that creates files."""
    coder_state: CoderState = state.get("coder_state")
    if coder_state is None:
        coder_state = CoderState(task_plan=state["task_plan"], current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        print(f"Completed all {len(steps)} tasks")
        return {"coder_state": coder_state, "status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    print(f"Working on: {current_task.filepath}")
    
    # Simplified prompt without reading existing content to reduce token usage
    system_prompt = "You are a web developer. Create complete, functional files."
    user_prompt = (
        f"Create {current_task.filepath} for: {coder_state.task_plan.plan.description}\n"
        f"Task: {current_task.task_description}\n"
        "Write complete file content using write_file(path, content)."
    )

    coder_tools = [write_file, file_exists]
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