from fastapi import FastAPI
from app.endpoints import submissions, languages, health
from app.core.state import get_app_version

app = FastAPI(
    title="KodeJudge API",
    description="A powerful and modern code execution engine, inspired by judge0.",
    version=get_app_version(),
)

app.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
app.include_router(languages.router, prefix="/languages", tags=["Languages"])
app.include_router(health.router, prefix="/health", tags=["Health"])


@app.get("/", summary="Root Endpoint", description="Welcome to KodeJudge API")
async def root():
    return {
        "message": "Welcome to KodeJudge API",
        "version": get_app_version(),
        "documentation": "/docs",
        "redoc": "/redoc",
    }
