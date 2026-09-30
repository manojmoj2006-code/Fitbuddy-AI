"""Central configuration. Values come from environment variables or a .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")

# The docs mention GOOGLE_API_KEY; GEMINI_API_KEY is the current name. Either works.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

# Gemini 1.5 models have been retired, so the defaults are the 2.5 generation.
# "Pro" writes and updates workout plans, "Flash" writes quick nutrition tips.
PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'fitbuddy.db'}")

TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
