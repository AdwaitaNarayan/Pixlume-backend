import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from app.database.connection import init_db
from app.routes.photos import router as photos_router
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Pixlume API",
    description="Backend API for Pixlume – a high-resolution photography platform.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS – allow the Next.js frontend (and any local dev origin) to call us
# ---------------------------------------------------------------------------
origins_env = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,https://pixlume.online,https://www.pixlume.online")
allow_origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
# Add versions without trailing slashes just in case
allow_origins += [o[:-1] for o in allow_origins if o.endswith("/")]
allow_origins = list(set(allow_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router, prefix="/admin", tags=["Admin Auth"])
app.include_router(photos_router, prefix="/photos", tags=["Photos"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "Pixlume API"}

