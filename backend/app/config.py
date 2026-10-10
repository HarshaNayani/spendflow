"""Central configuration, read from environment variables (.env supported)."""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spendflow.db")
# Render and Heroku hand out postgres:// URLs; SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "8"))

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]

SEED_DEMO = os.getenv("SEED_DEMO", "true").lower() == "true"
HIGH_AMOUNT_THRESHOLD = float(os.getenv("HIGH_AMOUNT_THRESHOLD", "50000"))

CATEGORIES = [
    "Travel",
    "Food",
    "Software",
    "Office Supplies",
    "Equipment",
    "Marketing",
    "Utilities",
    "Training",
    "Other",
]
