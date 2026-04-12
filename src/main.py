from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import load_settings
from src.database import create_session_factory
from src.services.github import GitHubOAuthClient

settings = load_settings()
session_factory = create_session_factory(settings)
github_client = GitHubOAuthClient(
    client_id=settings.github.client_id,
    client_secret=settings.github.client_secret,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Auth Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.server.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


from src.api.auth import router as auth_router

app.include_router(auth_router)
