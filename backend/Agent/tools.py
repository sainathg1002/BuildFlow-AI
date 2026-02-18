import os
from langchain_core.tools import tool

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspaces"))

def safe_path(path: str):
    """Ensure path is within workspace directory."""
    clean = (path or "").strip()
    if not clean:
        raise ValueError("Path cannot be empty")

    if os.path.isabs(clean):
        full_path = os.path.abspath(clean)
    else:
        full_path = os.path.abspath(os.path.join(BASE_DIR, clean))

    if os.path.commonpath([full_path, BASE_DIR]) != BASE_DIR:
        raise ValueError("Access outside workspace not allowed")

    return full_path


@tool
def read_file(path: str) -> str:
    """Read the content of a file at the given path."""
    try:
        path = safe_path(path)
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file at the given path. Creates directories if needed."""
    try:
        path = safe_path(path)
        dirname = os.path.dirname(path)
        os.makedirs(dirname, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_files(path: str = ".") -> str:
    """List files and directories in the given path."""
    try:
        path = safe_path(path)
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing files: {e}"


@tool
def file_exists(path: str) -> str:
    """Check if a file exists."""
    try:
        path = safe_path(path)
        return "true" if os.path.exists(path) else "false"
    except Exception as e:
        return "false"


@tool
def get_current_directory() -> str:
    """Get the current working directory."""
    return os.getcwd()
