from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()

from app.api.router import router
from app.core.config import settings


def _parse_cors_origins(value: str | None) -> list[str]:
    """
    Parse cors_allowed_origins from settings (loaded from backend/.env via Pydantic).
    Formats:
      - "http://localhost:3000,http://127.0.0.1:3000"
      - "http://localhost:3000"
      - None/"" -> []
    """
    if not value:
        return []
    return [o.strip() for o in value.split(",") if o.strip()]


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

# CORS (settings-driven; reads backend/.env)
cors_origins = _parse_cors_origins(settings.cors_allowed_origins)
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to FlowRisk API"}
