import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time
from hashlib import sha256
from threading import Lock

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import shutil
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


try:
    # Works when launched from project root: uvicorn backend.api:app
    from backend.Agent.graph import agent
except ModuleNotFoundError:
    # Works when launched from backend folder: uvicorn api:app
    from Agent.graph import agent


app = FastAPI()


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
    return list(dict.fromkeys(defaults + origins))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_origin_regex=os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving generated workspaces
WORKSPACES_DIR = os.path.join(os.path.dirname(__file__), "workspaces")
os.makedirs(WORKSPACES_DIR, exist_ok=True)
app.mount("/workspaces", StaticFiles(directory=WORKSPACES_DIR), name="workspaces")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API is running", "docs": "/docs"}

class AgentRequest(BaseModel):
    prompt: str
    recursion_limit: int = 12

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Try again later."}
    )


def _build_project_response(project_folder: str):
    if not os.path.exists(project_folder):
        return None

    zip_path = f"{project_folder}.zip"
    shutil.make_archive(project_folder.replace(".zip", ""), "zip", project_folder)

    project_name = os.path.basename(project_folder)
    app_url = f"/workspaces/{project_name}/index.html"

    return {
        "download": zip_path.replace("\\", "/"),
        "project": project_folder,
        "app_url": app_url,
    }


_RESPONSE_CACHE: dict[str, dict] = {}
_RESPONSE_CACHE_LOCK = Lock()
_RESPONSE_CACHE_MAX = max(10, int(os.getenv("GENERATION_CACHE_MAX", "200")))
_RESPONSE_CACHE_TTL_SECONDS = max(30, int(os.getenv("GENERATION_CACHE_TTL_SECONDS", "900")))


def _normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.strip().lower().split())


def _cache_key(prompt: str, recursion_limit: int) -> str:
    payload = f"{_normalize_prompt(prompt)}|{recursion_limit}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _cache_get(key: str):
    now = time.time()
    with _RESPONSE_CACHE_LOCK:
        item = _RESPONSE_CACHE.get(key)
        if not item:
            return None
        if now > item["expires_at"]:
            _RESPONSE_CACHE.pop(key, None)
            return None

        response = item["response"]
        project_folder = response.get("project")
        if project_folder and os.path.exists(project_folder):
            return dict(response)

        _RESPONSE_CACHE.pop(key, None)
        return None


def _cache_set(key: str, response: dict):
    with _RESPONSE_CACHE_LOCK:
        if len(_RESPONSE_CACHE) >= _RESPONSE_CACHE_MAX:
            oldest_key = next(iter(_RESPONSE_CACHE))
            _RESPONSE_CACHE.pop(oldest_key, None)
        _RESPONSE_CACHE[key] = {
            "response": dict(response),
            "expires_at": time.time() + _RESPONSE_CACHE_TTL_SECONDS,
        }


def _find_latest_workspace(since_time: float):
    latest_path = None
    latest_mtime = since_time

    for name in os.listdir(WORKSPACES_DIR):
        path = os.path.join(WORKSPACES_DIR, name)
        if not os.path.isdir(path):
            continue

        index_file = os.path.join(path, "index.html")
        if not os.path.exists(index_file):
            continue

        mtime = os.path.getmtime(path)
        if mtime >= latest_mtime:
            latest_mtime = mtime
            latest_path = path

    return latest_path

@app.post("/generate")
@limiter.limit("5/minute")
def generate_project(request: Request, req: AgentRequest):
    if req.recursion_limit > 25:
        raise HTTPException(status_code=400, detail="Recursion limit too high (max: 25)")
    if req.recursion_limit < 1:
        raise HTTPException(status_code=400, detail="Recursion limit must be at least 1")

    key = _cache_key(req.prompt, req.recursion_limit)
    cached = _cache_get(key)
    if cached:
        cached["cached"] = True
        return cached

    timeout_seconds = int(os.getenv("GENERATION_TIMEOUT_SECONDS", "180"))
    request_started = time.time()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        agent.invoke,
        {"user_prompt": req.prompt},
        {"recursion_limit": req.recursion_limit}
    )

    try:
        result = future.result(timeout=timeout_seconds)
        executor.shutdown(wait=False, cancel_futures=True)

        plan = result.get("plan")
        if not plan and result.get("task_plan"):
            plan = getattr(result["task_plan"], "plan", None)
        if not plan and result.get("coder_state"):
            task_plan = getattr(result["coder_state"], "task_plan", None)
            plan = getattr(task_plan, "plan", None) if task_plan else None

        if not plan or not getattr(plan, "files", None):
            return {"error": "Failed to generate project"}
        
        project_folder = os.path.dirname(plan.files[0].path)
        project_response = _build_project_response(project_folder)
        if not project_response:
            return {"error": "Project folder not created"}

        _cache_set(key, project_response)
        return project_response
    
    except FuturesTimeoutError:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)

        latest_workspace = _find_latest_workspace(request_started)
        if latest_workspace:
            project_response = _build_project_response(latest_workspace)
            if project_response:
                project_response["warning"] = (
                    f"Generation exceeded {timeout_seconds} seconds, "
                    "but app files were created."
                )
                project_response["timed_out"] = True
                _cache_set(key, project_response)
                return project_response

        return {"error": f"Execution timeout - request took longer than {timeout_seconds} seconds"}
    
    except Exception as e:
        executor.shutdown(wait=False, cancel_futures=True)
        return {"error": str(e)}
