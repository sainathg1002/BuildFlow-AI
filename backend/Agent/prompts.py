import json
from .states import Plan, TaskPlan
def planner_prompt(user_prompt: str) -> str:
    schema = json.dumps(Plan.model_json_schema(), indent=2)
    return f"""
Create a structured plan for a modern web app based on the user request.

User Request: {user_prompt}

Return ONLY valid JSON matching this schema:
{schema}

For files, use simple relative paths like "index.html", "style.css", "script.js". Do not include project folders in paths.
Techstack should be "html, css, javascript" for simple web apps.
Keep it concise. Return JSON only. No explanation.
"""


def architect_prompt(plan: Plan) -> str:
    schema = json.dumps(TaskPlan.model_json_schema(), indent=2)
    return f"""
You are the ARCHITECT agent.

Create one implementation task per file in the project plan.
Order the tasks based on dependencies (e.g., HTML before JS).
For each task:
- filepath: exact from plan.files.path
- task_description: detailed instructions on what to implement in that file, based on the plan features and description.
- dependencies: list of other filepaths this task depends on (e.g., JS depends on HTML).

Project Plan: {plan.model_dump_json(indent=2)}

Return ONLY valid JSON matching this schema:
{schema}
Return JSON only. No explanation.
"""


def coder_system_prompt() -> str:
    return """
You are a senior frontend engineer.

Requirements:
- Modern SaaS-style UI
- Use Flexbox or Grid
- Responsive layout
- Primary color: #2563eb
- Background: #f8fafc
- Border radius: 12px
- Soft shadows
- Smooth hover transitions
- Clean typography scale

Return only full file content.
No markdown.
No explanation.
"""
