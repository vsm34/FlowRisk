from fastapi import FastAPI

from app.api.router import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# Include API router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to FlowRisk API"}
