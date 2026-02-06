import os
from langchain_core.tools import tool

@tool
def read_file(path: str) -> str:
    """Read the content of a file at the given path."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file at the given path. Creates directories if needed."""
    try:
        dirname = os.path.dirname(path)
        if dirname:
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
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing files: {e}"

@tool
def file_exists(path: str) -> str:
    """Check if a file exists."""
    return "true" if os.path.exists(path) else "false"

@tool
def get_current_directory() -> str:
    """Get the current working directory."""
    return os.getcwd()