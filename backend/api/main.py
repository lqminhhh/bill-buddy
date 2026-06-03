import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, expenses, share, trips
from api.schemas import HealthResponse


def _allowed_origins() -> list[str]:
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="Bill Buddy API",
    version="0.2.0",
    description="JSON API for the Bill Buddy expense tracker.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(expenses.router)
app.include_router(share.router)


@app.get("/healthz", response_model=HealthResponse, tags=["meta"])
def healthz() -> HealthResponse:
    return HealthResponse(ok=True)
