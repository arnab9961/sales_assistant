# Vercel ASGI entry point for FastAPI
# Vercel looks for the `app` variable in this file.
import sys
import os

# Ensure the project root is on the path so `app` package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: F401  — Vercel uses this `app` object
