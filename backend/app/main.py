from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, SEED_DEMO
from .database import Base, engine
from .routers import ai, auth, dashboard, expenses
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if SEED_DEMO:
        seed_if_empty()
    yield


app = FastAPI(
    title="SpendFlow API",
    description="Expense approval workflow with role-based access and AI checks.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Any Vercel preview or production URL, handy for the demo.
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(ai.router)


@app.get("/", tags=["health"])
def root():
    return {"service": "SpendFlow API", "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
