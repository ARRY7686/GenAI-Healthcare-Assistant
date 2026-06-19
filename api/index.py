"""Vercel Python serverless entrypoint.

Vercel's Python runtime serves the module-level `app` (an ASGI callable). `vercel.json`
rewrites every `/api/*` request to this function; the FastAPI app (whose routes are already
prefixed `/api`) handles them. `backend/` is bundled via `includeFiles` in vercel.json.
"""

import os
import sys

# Make the FastAPI package (backend/app) importable from the function bundle.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app  # noqa: E402  — ASGI app served by Vercel

__all__ = ["app"]
