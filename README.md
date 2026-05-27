# Acme ERP — example deployment on the lambda-erp open-core

A minimal, **working example of a customer deployment** built on top of the
published Lambda ERP packages. It depends on the **published** artifacts — it
does **not** fork or vendor the core repo:

| Layer | Depends on | From |
|-------|-----------|------|
| Backend | `lambda-erp==0.1.2` | PyPI |
| Frontend | `@lambda-development/erp-core@^0.1.2` | npm |

It doubles as the **template** a real (private) customer repo copies. Core fixes
arrive via a version bump in `pyproject.toml` / `frontend/package.json` — never a
merge into a fork.

> Scaffolded as Phase D of the core's packaging plan
> (`docs/packaging-distribution-plan.md` in the core repo). See **Status** below
> for what's verified vs. still TODO.

## What it customizes

All overrides go through the public extension seams — zero core files touched.

**Backend** (`acme/`, loaded via `LAMBDA_ERP_PLUGINS=acme`):
- `acme/sales_invoice.py` — `AcmeSalesInvoice(SalesInvoice)` overriding
  `_get_gl_entries` (the **replace** seam).
- `acme/plugin.py` — `register()` wires it up with `register_doctype("Sales
  Invoice", AcmeSalesInvoice)` and adds a `register_hook("Sales
  Invoice:after_submit", …)` side-effect (the **extend** seam).

**Frontend** (`frontend/src/`):
- `plugin.tsx` — `configureBranding` (name + brand colour), `configureApiBase`,
  `registerComponent("Dashboard", AcmeDashboard)`, and a `registerNavItem`.
- `dashboard.tsx` — the replacement dashboard.
- `brand.css` — overrides the `--brand` CSS token for first paint.

## Layout

```
lambda-erp-example/
  pyproject.toml          # lambda-erp==0.1.2  (the backend core)
  app.py                  # ASGI entry: core app + serves THIS frontend build
  acme/
    plugin.py             # register() — overrides + hooks
    sales_invoice.py      # AcmeSalesInvoice(SalesInvoice)
  frontend/
    package.json          # @lambda-development/erp-core ^0.1.2 + its peers
    tailwind.config.ts    # scans the core dist + uses its preset
    src/{main,plugin,dashboard}.tsx, brand.css
  Dockerfile              # one container: builds frontend, serves via backend
  .env.example
```

## Run it

### Local dev (two processes)

```bash
# 1) Backend — installs lambda-erp from PyPI + the acme plugin
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env                 # LAMBDA_ERP_PLUGINS=acme is the key line
export $(grep -v '^#' .env | xargs)  # or use your preferred env loader
uvicorn app:app --reload --port 8000

# 2) Frontend — installs the core npm lib + peers, proxies /api to :8000
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

### One container (production shape)

```bash
docker build -t acme-erp .
docker run -p 8000:8000 -v acme-data:/data acme-erp   # http://localhost:8000
```

The image builds the frontend (core npm package + overrides) and serves it from
the backend (core pip package + the acme plugin) at one origin.

## How the pieces fit

- **Plugin loading:** the core reads `LAMBDA_ERP_PLUGINS` on startup and calls
  each module's `register()`. That's the single entry point for backend
  overrides + hooks.
- **Serving the frontend:** the core only auto-serves a frontend that sits next
  to its own installed package, so this repo's `app.py` imports the core
  FastAPI `app` and mounts **this** repo's `frontend/dist` (with an SPA
  fallback). Run the backend from the repo root so the relative path resolves.
- **Styling ("consumer scans source"):** our own Tailwind build generates the
  utilities, scanning the core's built JS (`tailwind.config.ts` `content`) and
  using its shared `tailwind-preset`. We import the core's `styles.css` (tokens
  + base layers) and override the `--brand` token.

## Upgrading the core

Bump both versions in lockstep and rebuild:
- `pyproject.toml` → `lambda-erp==X.Y.Z`
- `frontend/package.json` → `@lambda-development/erp-core@^X.Y.Z`

The extension seams are semver-governed; a breaking change there is a major bump.

## Status

**Scaffolded — not yet built end-to-end against the published packages.** Before
treating this as the canonical template, do one real build to confirm the
published `0.1.2` artifacts install and compose:

- [ ] `pip install -e .` resolves `lambda-erp==0.1.2` and `uvicorn app:app` boots
  (plugin loads, `[plugins] loading acme` in the logs).
- [ ] `cd frontend && npm install && npm run build` produces `frontend/dist`
  importing `@lambda-development/erp-core` (and `tsc -b` passes).
- [ ] `docker build .` succeeds and the running container serves the branded UI
  at `/` with the custom dashboard.
- [ ] Decide: keep as a plain example, or convert to a `cookiecutter` template
  (open question from the core's Phase D plan).

Possible core improvement surfaced while scaffolding: the core could accept an
env-configurable frontend-dist path so a customer wouldn't need the `app.py`
static-mount shim. Tracked against the core, not here.
