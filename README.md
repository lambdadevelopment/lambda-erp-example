# Acme ERP — example deployment on the lambda-erp open-core

A minimal, **working example of a customer deployment** built on top of the
published Lambda ERP packages. It depends on the **published** artifacts — it
does **not** fork or vendor the core repo:

| Layer | Depends on | From |
|-------|-----------|------|
| Backend | `lambda-erp==0.1.31` | PyPI |
| Frontend | `@lambda-development/erp-core@^0.1.31` | npm |

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
- `acme/pdf_templates/document.html` — a custom invoice/document **PDF**
  template, wired via `register_pdf_template_dir(…)` in `register()` (the **PDF
  override** seam). It started as a copy of the core template and gets the same
  render context, so you just restyle the same data (logo, letterhead, CSS).
  Requires a `lambda-erp` release that includes `register_pdf_template_dir`
  (bump the pin to that version).

**Frontend** (`frontend/src/`):
- `plugin.tsx` — `configureBranding` (name + brand colour), `configureApiBase`,
  `registerComponent("Dashboard", AcmeDashboard)`, and a `registerNavItem`.
- `dashboard.tsx` — the replacement dashboard.
- `brand.css` — overrides the `--brand` CSS token for first paint.

## Layout

```
lambda-erp-example/
  pyproject.toml          # lambda-erp==0.1.31  (the backend core)
  app.py                  # ASGI entry: core app + serves THIS frontend build
  acme/
    plugin.py             # register() — overrides + hooks + PDF template dir
    sales_invoice.py      # AcmeSalesInvoice(SalesInvoice)
    pdf_templates/
      document.html       # custom PDF (register_pdf_template_dir)
  frontend/
    package.json          # @lambda-development/erp-core ^0.1.31 + its peers
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

> **Going to production?** Read [docs/deploying.md](docs/deploying.md) first —
> it covers the one thing that bites: **persistence**. SQLite needs a real disk
> (it can't get file locks on a network share like Azure Files), so on a managed
> container platform you point `LAMBDA_ERP_DB` at **PostgreSQL** instead. Also
> covers the single-replica constraint and the stable `JWT_SECRET_KEY`.

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

## License

MIT. See [LICENSE](LICENSE) for the full text.

## Trademarks and affiliations

Lambda ERP and lambda.dev are product and trade names of TORUS INVESTMENTS AG. It is not affiliated with, endorsed by, or sponsored by OpenAI, Anthropic, SAP, Oracle, Microsoft, or any other company named in this repository. SAP, Business One, S/4HANA, Oracle, NetSuite, Microsoft, Dynamics, OpenAI, GPT, Anthropic, and Claude are trademarks of their respective owners and are referenced here only for descriptive and comparative purposes (nominative fair use). We interoperate with OpenAI and Anthropic APIs as a customer like anyone else; you supply your own API keys.
