"""
Backend API Server Startup Script
Run with: uvicorn backend.api:app --reload
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)