def planner_prompt(user_prompt: str) -> str:
    PLANNER_PROMPT = f"""
You are the PLANNER agent. Convert the user prompt into a COMPLETE engineering project plan.

User request:
{user_prompt}
    """
    return PLANNER_PROMPT


def architect_prompt(plan: str) -> str:
    ARCHITECT_PROMPT = f"""
You are the ARCHITECT agent. Given this project plan, break it down into simple implementation tasks.

Create a TaskPlan with implementation_steps. Each step should have:
- filepath: the file to create/modify
- task_description: what to implement in that file

Keep tasks simple and focused. For a web app, typically create:
1. HTML file with structure
2. CSS file with styling  
3. JavaScript file with functionality
4. README file with documentation

Project Plan:
{plan}
    """
    return ARCHITECT_PROMPT


def coder_system_prompt() -> str:
    CODER_SYSTEM_PROMPT = """
You are the CODER agent.
Generate production-ready web files.
Rules:
- Return only the full file content.
- No markdown fences and no extra explanation.
- Keep IDs, class names, and function names consistent across files.
- Prefer simple, readable, dependency-free code.
    """
    return CODER_SYSTEM_PROMPT
