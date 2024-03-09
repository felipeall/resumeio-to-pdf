import uvicorn
from fastapi import FastAPI

from app.api.api import router

app = FastAPI(title="Resume.io to PDF")
app.include_router(router)


if __name__ == "__main__":
    """Instantiate the application webserver"""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["app", "templates"])
