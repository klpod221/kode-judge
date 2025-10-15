from fastapi import FastAPI
from app.endpoints import submissions, languages

app = FastAPI(
    title="KodeJudge API",
    description="A powerful and modern code execution engine, clone of Judge0",
    version="1.0.0",
)

app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
app.include_router(languages.router, prefix="/languages", tags=["languages"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to KodeJudge API",
        "documentation": "/docs",
        "redoc": "/redoc",
    }
