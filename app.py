"""ASGI entry for the example deployment.

Imports the core FastAPI app (which loads the `acme` plugin on startup via
LAMBDA_ERP_PLUGINS) and serves THIS repo's frontend build. The core only
auto-serves a frontend that sits next to its own installed package, so a
customer deployment that builds its own bundle wires up static serving here.

Run from the repo root: `uvicorn app:app` (the frontend/dist path is relative
to this file, not to the installed core package).
"""
import os

# Ensure our plugin loads even if the runtime forgot to set it. Real deploys set
# this in the environment (see .env.example / Dockerfile).
os.environ.setdefault("LAMBDA_ERP_PLUGINS", "acme")

from fastapi import HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from api.main import app  # noqa: E402  — env must be set before this import

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    root = os.path.realpath(FRONTEND_DIST)
    index_html = os.path.join(root, "index.html")

    # SPA fallback: real files resolve as-is; everything else (except API/WS)
    # serves index.html so the client-side router takes over. Mirrors the core's
    # own fallback, pointed at our build.
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith(("api/", "ws/")):
            raise HTTPException(status_code=404, detail="Not Found")
        if full_path:
            candidate = os.path.realpath(os.path.join(root, full_path))
            if candidate.startswith(root + os.sep) and os.path.isfile(candidate):
                return FileResponse(candidate)
        return FileResponse(index_html)
