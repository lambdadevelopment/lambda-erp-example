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

# Behind a TLS proxy the app sees plain http requests. MCP / OAuth discovery
# (how lambda.dev, Claude or ChatGPT connect to this ERP) must advertise the
# public https address, so reuse OAUTH_REDIRECT_BASE when it is set. An explicit
# MCP_PUBLIC_URL still wins; local development uses the request's own address.
if os.environ.get("OAUTH_REDIRECT_BASE"):
    os.environ.setdefault("MCP_PUBLIC_URL", os.environ["OAUTH_REDIRECT_BASE"])

from fastapi import HTTPException  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from api.main import app  # noqa: E402  — env must be set before this import



class _ImmutableStaticFiles(StaticFiles):
    """Serve content-hashed build assets with a long-lived immutable cache.

    Vite fingerprints every file under /assets, so the bytes at a given URL
    never change: a new build emits new filenames. index.html stays `no-cache`
    (below) so a new build is still picked up. Mirrors the core's own serving.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
        return response


FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", _ImmutableStaticFiles(directory=assets_dir), name="assets")

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
        # `no-cache`: always revalidate the unhashed shell, so a reload after an
        # upgrade never serves an old index.html pointing at old asset URLs.
        return FileResponse(index_html, headers={"Cache-Control": "no-cache"})
